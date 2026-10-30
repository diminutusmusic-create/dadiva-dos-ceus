"""Vídeos longos de leitura/oração: paisagem realista 2.5D + versículo na tela.
Uso: python motor/leitura.py leituras/xxx.json [--ate SEGUNDOS]
Saída: videos-longos/<slug>.mp4 (1920x1080)

Formato:
{"titulo": "Salmo 23", "subtitulo": "O Senhor é o meu pastor", "voz": "pm_alex", "velocidade": .85,
 "pausa_verso": 2.4, "ambiente": "riacho"|"chuva"|"noite"|null,
 "blocos": [{"cenario": "pastos_amanhecer", "efeito": ["nevoa", "luz", "estrelas"],
             "versos": [{"ref": "Salmo 23:1", "texto": "..."}]}],
 "fim": "Dádiva dos Céus"}
"""
import json, math, os, subprocess, sys, random
import numpy as np, cv2, skia, soundfile as sf
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from episodio import trilha, lp, SR, MODELOS

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W, H, FPS = 1920, 1080, 30
FONTES = f'{RAIZ}/fontes'
def fonte(nome, tam): return skia.Font(skia.Typeface.MakeFromFile(f'{FONTES}/{nome}.ttf'), tam)

# ------------------------------------------------------------ cenários 2.5D
class Cena:
    OVER = 1.12
    def __init__(self, nome):
        base = f'{RAIZ}/arte/paisagens/{nome}'
        img = cv2.imread(base + '.png', cv2.IMREAD_COLOR)
        dep = cv2.imread(base + '_depth.png', cv2.IMREAD_GRAYSCALE)
        if dep is None: dep = np.tile(np.linspace(0, 255, img.shape[0])[:, None], (1, img.shape[1])).astype(np.uint8)
        BW, BH = int(W * self.OVER), int(H * self.OVER)
        img = cv2.resize(img, (BW, BH), interpolation=cv2.INTER_LANCZOS4)
        blur = cv2.GaussianBlur(img, (0, 0), 2.0)
        self.img = cv2.addWeighted(img, 1.35, blur, -.35, 0)  # nitidez leve
        d = cv2.resize(dep, (BW, BH), interpolation=cv2.INTER_CUBIC).astype(np.float32) / 255
        d = cv2.GaussianBlur(d, (0, 0), 9)
        self.d = (d - d.min()) / (d.max() - d.min() + 1e-6)  # 1 = perto
        gx, gy = np.meshgrid(np.arange(W, dtype=np.float32), np.arange(H, dtype=np.float32))
        self.gx, self.gy = gx, gy
        self.dd = cv2.resize(self.d, (W, H))
        self.mx, self.my = (BW - W) / 2, (BH - H) / 2
        r = random.Random(hash(nome) & 0xffff)
        self.fase = r.uniform(0, 6.28); self.dir = r.choice([-1, 1])

    def frame(self, t):
        # câmera lenta: deriva lateral + leve zoom + respiração
        k = .5 + .5 * math.sin(t * .045 + self.fase)
        px = self.dir * (k - .5) * 46          # deslocamento de paralaxe (px no plano perto)
        py = math.sin(t * .03 + self.fase) * 10
        z = 1 - .035 * (.5 + .5 * math.sin(t * .025 + self.fase * .7))
        cx, cy = W / 2, H / 2
        mx = (self.gx - cx) * z + cx + self.mx - self.dd * px + px * .35
        my = (self.gy - cy) * z + cy + self.my - self.dd * py + py * .35
        return cv2.remap(self.img, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)

# ------------------------------------------------------------ efeitos
class Nevoa:
    def __init__(self, seed=3):
        rng = np.random.default_rng(seed)
        n = rng.random((18, 32)).astype(np.float32)
        n = cv2.resize(n, (W * 2, H), interpolation=cv2.INTER_CUBIC)
        n = cv2.GaussianBlur(n, (0, 0), 60)
        n = (n - n.min()) / (n.max() - n.min())
        grad = np.linspace(.2, 1, H, dtype=np.float32)[:, None] ** 1.5
        self.n = (n * grad)[..., None]
    def aplica(self, f, t, forca=.22):
        o = int(t * 14) % W
        m = self.n[:, o:o + W] * forca
        return f * (1 - m) + 225 * m

class Poeira:
    def __init__(self, n=70, seed=7):
        r = random.Random(seed)
        self.p = [(r.uniform(0, W), r.uniform(0, H), r.uniform(4, 14), r.uniform(1.5, 4), r.uniform(0, 6.28)) for _ in range(n)]
    def draw(self, c, t, a=1.0):
        for x, y, v, s, ph in self.p:
            xx = (x + t * v + math.sin(t * .3 + ph) * 30) % W
            yy = (y - t * v * .6) % H
            al = int(a * 90 * (.5 + .5 * math.sin(t * .8 + ph)))
            c.drawCircle(xx, yy, s, skia.Paint(AntiAlias=True, Color=skia.Color(255, 236, 190, al),
                         MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, s * .8)))

class Estrelas:
    def __init__(self, n=160, seed=11):
        r = random.Random(seed)
        self.s = [(r.uniform(0, W), r.uniform(0, H * .45), r.uniform(.8, 2.2), r.uniform(0, 6.28), r.uniform(.5, 2)) for _ in range(n)]
    def draw(self, c, t, a=1.0):
        for x, y, s, ph, sp in self.s:
            al = int(a * 140 * (.4 + .6 * (.5 + .5 * math.sin(t * sp + ph))))
            c.drawCircle(x, y, s, skia.Paint(AntiAlias=True, Color=skia.Color(255, 255, 240, al)))

def vinheta():
    y, x = np.mgrid[0:H, 0:W].astype(np.float32)
    r = np.sqrt(((x - W / 2) / (W * .62)) ** 2 + ((y - H / 2) / (H * .62)) ** 2)
    v = np.clip(1 - (r - .55) * .9, .45, 1)
    # escurece a faixa do texto para leitura
    band = 1 - .38 * np.exp(-((y - H * .70) / (H * .17)) ** 2)
    return (v * band)[..., None]

def grade(f):
    # tons quentes e noturnos, contraste suave
    f = f * np.array([0.92, 0.97, 1.05], np.float32)  # BGR: leve âmbar
    return f

# ------------------------------------------------------------ texto
def quebra(palavras, font, maxw):
    linhas = [[]]; larg = 0; sp = font.measureText(' ')
    for i, w in enumerate(palavras):
        lw = font.measureText(w)
        if linhas[-1] and larg + sp + lw > maxw: linhas.append([]); larg = 0
        linhas[-1].append(i); larg += (sp if larg else 0) + lw
    return linhas

def desenha_verso(c, verso, t0, t1, t, fs, fr):
    a = min(1, (t - t0 + .8) / 1.2, (t1 + 1.6 - t) / 1.2)
    if a <= 0: return
    pal = verso['texto'].split()
    # tempo de cada palavra proporcional ao tamanho (+ pausa em pontuação)
    pes = [len(w) + 2 + (4 if w[-1] in ',;:' else 0) + (6 if w[-1] in '.!?' else 0) for w in pal]
    cum = np.cumsum([0] + pes) / sum(pes)
    prog = (t - t0) / max(.1, t1 - t0)
    atual = int(np.searchsorted(cum, prog, side='right') - 1) if 0 <= prog < 1 else -1
    linhas = quebra(pal, fs, W * .68); sp = fs.measureText(' '); lh = fs.getSize() * 1.32
    y0 = H * .70 - (len(linhas) - 1) * lh / 2 + fs.getSize() * .35
    sombra = skia.Paint(AntiAlias=True, Color=skia.Color(0, 0, 0, int(160 * a)),
                        MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 6))
    for li, linha in enumerate(linhas):
        txt = [pal[i] for i in linha]
        lw = sum(fs.measureText(w) for w in txt) + sp * (len(txt) - 1)
        x = W / 2 - lw / 2; y = y0 + li * lh
        for i in linha:
            w = pal[i]; ww = fs.measureText(w)
            lido = i < atual or prog >= 1
            if i == atual: cor = skia.Color(255, 226, 160, int(255 * a))
            elif lido: cor = skia.Color(255, 250, 240, int(235 * a))
            else: cor = skia.Color(255, 250, 240, int(175 * a))
            c.drawString(w, x + 2, y + 3, fs, sombra)
            c.drawString(w, x, y, fs, skia.Paint(AntiAlias=True, Color=cor))
            x += ww + sp
    ref = verso['ref']; rw = fr.measureText(ref)
    yref = y0 + len(linhas) * lh + 8
    c.drawString(ref, W / 2 - rw / 2, yref, fr, skia.Paint(AntiAlias=True, Color=skia.Color(230, 205, 150, int(200 * a))))

def centro(c, txt, y, font, cor, a):
    w = font.measureText(txt)
    c.drawString(txt, W / 2 - w / 2 + 2, y + 3, font, skia.Paint(AntiAlias=True, Color=skia.Color(0, 0, 0, int(150 * a)),
                 MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 6)))
    c.drawString(txt, W / 2 - w / 2, y, font, skia.Paint(AntiAlias=True, Color=skia.Color(*cor, int(255 * a))))

# ------------------------------------------------------------ áudio
def falar(textos, voz, vel):
    """Voz em velocidade natural; a calma vem das pausas entre frases (aprovado: Alex natural)."""
    import re
    from kokoro_onnx import Kokoro
    k = Kokoro(f'{MODELOS}/kokoro-v1.0.onnx', f'{MODELOS}/voices-v1.0.bin')
    out = []
    for tx in textos:
        partes = [p.strip() for p in re.split(r'(?<=[,;:.!?])\s+', tx.replace('SENHOR', 'Senhor')) if p.strip()]
        seg = []
        for p in partes:
            s, sr = k.create(p, voice=voz, speed=vel, lang='pt-br')
            s = np.asarray(s, np.float32); nz = np.where(np.abs(s) > .01)[0]; s = s[max(0, nz[0] - 200):nz[-1] + 2500]
            n = int(len(s) * SR / sr); s = np.interp(np.linspace(0, len(s) - 1, n), np.arange(len(s)), s).astype(np.float32)
            seg += [s, np.zeros(int(SR * (.9 if p[-1] in '.!?' else .45)), np.float32)]
        s = np.concatenate(seg[:-1])
        out.append(sala(s / (np.abs(s).max() + 1e-6) * .85))
    return out

def sala(s):
    """Calor + leve ambiente de sala (mesmo tratamento da amostra aprovada)."""
    import tempfile
    a, b = tempfile.mktemp(suffix='.wav'), tempfile.mktemp(suffix='.wav')
    sf.write(a, s, SR)
    subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-i', a, '-af',
                    'bass=g=2:f=150,aecho=0.8:0.6:45|90:0.10|0.06', b], check=True)
    r, _ = sf.read(b, dtype='float32'); os.remove(a); os.remove(b)
    return r / (np.abs(r).max() + 1e-6) * .85

def ambiente(tipo, total):
    rng = np.random.default_rng(9); n = int(total * SR)
    if tipo == 'chuva': return lp(rng.standard_normal(n), .3) * .045
    if tipo == 'riacho':
        # água corrente escura e suave: ruído filtrado só nos graves/médios + borbulhas senoidais esparsas
        from scipy.signal import butter, sosfilt
        sos = butter(4, [90, 700], btype='band', fs=SR, output='sos')
        x = sosfilt(sos, rng.standard_normal(n))
        x = x / (np.abs(x).max() + 1e-9)
        t = np.arange(n) / SR
        x *= .65 + .25 * np.sin(2 * np.pi * .07 * t) + .1 * np.sin(2 * np.pi * .23 * t + 1)
        b = np.zeros(n)
        for st in np.arange(0, total, .12):
            if rng.random() < .35:
                d = rng.uniform(.03, .08); m = int(d * SR); a = int((st + rng.random() * .1) * SR)
                tt = np.arange(m) / SR; f0 = rng.uniform(350, 900)
                ch = np.sin(2 * np.pi * (f0 * tt + 2500 * tt ** 2)) * np.sin(np.pi * tt / d) * rng.uniform(.2, .5)
                b[a:a + m] += ch[:max(0, n - a)]
        b = sosfilt(butter(2, 1800, fs=SR, output='sos'), b)
        return x * .022 + b * .012
    if tipo == 'noite':
        x = np.zeros(n); t = np.arange(int(.05 * SR)) / SR
        for st in np.arange(0, total, .9):
            if rng.random() < .55:
                a = int((st + rng.random() * .3) * SR)
                ch = np.sin(2 * np.pi * 4300 * t) * np.sin(np.pi * t / t[-1]) * .012
                x[a:a + len(ch)] += ch[:max(0, n - a)]
        return x + lp(rng.standard_normal(n), .05) * .01
    return np.zeros(n)

# ------------------------------------------------------------ montagem
def gerar(caminho, ate=None):
    R = json.load(open(caminho)); slug = os.path.splitext(os.path.basename(caminho))[0]
    voz, vel = R.get('voz', 'pm_alex'), R.get('velocidade', .85)
    pv = R.get('pausa_verso', 2.4)
    global FPS
    FPS = R.get('fps', FPS)
    versos = []
    for bi, b in enumerate(R['blocos']):
        for it in b.get('itens') or [dict(v, tipo='verso') for v in b['versos']]:
            versos.append((bi, dict({'tipo': 'verso'}, **it)))
    print('tts', len(versos), flush=True)
    _fal = falar([v['texto'] for _, v in versos if v['tipo'] != 'silencio'], voz, vel)
    audios = [np.zeros(int(v.get('dur', 60) * SR), np.float32) if v['tipo'] == 'silencio' else _fal.pop(0) for _, v in versos]
    INTRO = 7.0; t = INTRO; tl = []
    for (bi, v), a in zip(versos, audios):
        d = len(a) / SR; tl.append((bi, v, t, t + d)); t += d + (0 if v['tipo'] == 'silencio' else v.get('pausa', pv))
    FIM_T = t + R.get('cauda', 0) + 1.0; total = FIM_T + 8.0
    if ate: total = min(total, ate)
    # trocas de bloco
    inicio_bloco = {}
    for bi, v, a, b in tl: inicio_bloco.setdefault(bi, a)
    # áudio
    mix = np.zeros(int((total + 1) * SR), np.float32)
    for (bi, v, a, b), s in zip(tl, audios):
        i = int(a * SR); mix[i:i + len(s)] += s[:max(0, len(mix) - i)]
    mus = trilha(total + 1, 'paz') * .55
    amb = ambiente(R.get('ambiente'), total + 1)
    n = len(mix); mix = mix + mus[:n] + amb[:n]
    fade = np.ones(n); fo = int(4 * SR); fade[-fo:] = np.linspace(1, 0, fo)
    mix = (mix * fade)[:int(total * SR)]
    mix = mix / (np.abs(mix).max() + 1e-6) * .89
    os.makedirs(f'{RAIZ}/videos-longos', exist_ok=True)
    wav = f'/tmp/{slug}.wav'; sf.write(wav, mix, SR)
    # vídeo
    cenas = {}
    def cena(bi):
        nome = R['blocos'][bi]['cenario']
        if nome not in cenas: cenas[nome] = Cena(nome)
        return cenas[nome]
    nev, poe, est, vin = Nevoa(), Poeira(), Estrelas(), vinheta()
    fv, fr = fonte('Cormorant-Medium', 68), fonte('Cinzel', 30)
    ft, fsub, fm = fonte('Cinzel-Bold', 96), fonte('Cormorant-Medium', 54), fonte('Cinzel', 34)
    out = f'{RAIZ}/videos-longos/{slug}.mp4' if not ate else f'{RAIZ}/videos-longos/{slug}-preview.mp4'
    ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{W}x{H}',
                           '-r', str(FPS), '-i', '-', '-i', wav, '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '20',
                           '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '160k', '-shortest', '-movflags', '+faststart', out],
                          stdin=subprocess.PIPE)
    blocos_t = sorted(inicio_bloco.items(), key=lambda x: x[1])
    XF = 3.0
    nfr = int(total * FPS)
    for fi in range(nfr):
        tt = fi / FPS
        # bloco atual e anterior (crossfade antes do 1º verso do bloco)
        atual = 0
        for bi, st in blocos_t:
            if tt >= st - 1.5: atual = bi
        f = cena(atual).frame(tt).astype(np.float32)
        st = dict(blocos_t).get(atual, 0) - 1.5
        if atual > 0 and tt < st + XF:
            prev = max(b for b, s in blocos_t if b < atual)
            k = (tt - st) / XF; k = k * k * (3 - 2 * k)
            f = cena(prev).frame(tt).astype(np.float32) * (1 - k) + f * k
        efs = R['blocos'][atual].get('efeito', [])
        if 'nevoa' in efs: f = nev.aplica(f, tt)
        f = grade(f) * vin
        # fade de entrada / saída
        g = min(1, tt / 2.5, (total - tt) / 3)
        f = np.clip(f * g, 0, 255).astype(np.uint8)
        rgba = cv2.cvtColor(f, cv2.COLOR_BGR2RGBA)
        surf = skia.Surface(rgba)  # desenha direto no buffer
        with surf as c:
            if 'estrelas' in efs: est.draw(c, tt, g)
            if 'poeira' in efs or 'luz' in efs: poe.draw(c, tt, g)
            # abertura
            if tt < INTRO + 1:
                a = min(1, (tt - .8) / 1.5, (INTRO + .5 - tt) / 1.5)
                if a > 0:
                    centro(c, R['titulo'], H * .45, ft, (255, 244, 220), a)
                    centro(c, R.get('subtitulo', ''), H * .45 + 80, fsub, (240, 220, 175), a)
            for bi, v, a0, a1 in tl:
                if v['tipo'] == 'verso':
                    if a0 - 1 <= tt <= a1 + 2: desenha_verso(c, v, a0, a1, tt, fv, fr)
                elif v.get('rotulo') and a0 - 1 <= tt <= a1 + 1.5:
                    al = min(1, (tt - a0 + 1) / 1.5, (a1 + 1.5 - tt) / 1.5)
                    centro(c, v['rotulo'], H * .90, fr, (230, 205, 150), al * .75)
            if tt > FIM_T:
                a = min(1, (tt - FIM_T) / 1.5, (total - tt) / 1.5)
                centro(c, R.get('fim', 'Dádiva dos Céus'), H * .46, ft, (255, 244, 220), a)
                centro(c, 'Bíblia Livre (BLIVRE), CC BY 4.0', H * .46 + 70, fm, (230, 205, 150), a * .8)
        ff.stdin.write(cv2.cvtColor(rgba, cv2.COLOR_RGBA2BGR).tobytes())
        if fi % (FPS * 10) == 0: print(f'{tt:.0f}/{total:.0f}s', flush=True)
    ff.stdin.close(); ff.wait(); print('ok', out, f'{total:.1f}s')
    return out

if __name__ == '__main__':
    ate = float(sys.argv[sys.argv.index('--ate') + 1]) if '--ate' in sys.argv else None
    gerar(sys.argv[1], ate)
