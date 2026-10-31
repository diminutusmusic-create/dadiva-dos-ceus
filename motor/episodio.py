"""Gera um episódio a partir de um roteiro JSON.
Uso: python motor/episodio.py roteiros/xxx.json [--preview]
Saída: videos/<slug>.mp4 (1080x1920, 30 fps)

Formato do roteiro (v2):
{
  "titulo", "referencia", "trilha": "paz"|"tensao", "voz_narrador": "pm_alex",
  "elenco": {"noe": {"arte": "noe_100", "voz": "pm_santa", "velocidade": .9, "cor": "#fff3c4"}},
  "cenas": [
    {"cenario": "diluvio", "efeito": ["chuva", "ondas", "noite", "relampago", "luz"],
     "atores": [{"quem": "noe", "x": .5, "altura": .5, "olha": "esquerda", "entra": "direita"}],
     "objetos": [{"arte": "arca_100", "x": .5, "y": .8, "altura": .3, "anim": "flutua"|"nada"|"voa"|"balanca"}],
     "falas": [{"quem": "narrador", "texto": "...", "pausa": .5}]}
  ]
}
O formato antigo (cenario/personagens/falas no topo) continua funcionando.
"""
import json, math, os, re, subprocess, sys, random
import numpy as np, soundfile as sf
import skia
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from engine import W, H, FPS, font, text_center, ease, clamp, lerp, Dust
from cartoon_rig import Puppet, RIGS, cutout, to_skia

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SR = 44100
MODELOS = os.environ.get('KOKORO_DIR', f'{RAIZ}/modelos')
SAMP = skia.SamplingOptions(skia.FilterMode.kLinear, skia.MipmapMode.kLinear)

# ------------------------------------------------------------ legendas
def wrap(txt, maxc=20):
    lines = ['']
    for w in txt.split():
        if lines[-1] and len(lines[-1]) + 1 + len(w) > maxc: lines.append(w)
        else: lines[-1] = (lines[-1] + ' ' + w).strip()
    return lines

FUNC = {'e', 'o', 'a', 'os', 'as', 'um', 'uma', 'de', 'do', 'da', 'dos', 'das', 'em', 'no', 'na', 'com', 'para', 'por', 'que', 'só'}
def split_long(p):
    if len(wrap(p)) <= 2: return [p]
    w = p.split(); best = None
    for k in range(1, len(w)):
        L, R = ' '.join(w[:k]), ' '.join(w[k:])
        sc = abs(len(L) - len(R)) - (14 if L.endswith(',') else 0) + (25 if w[k - 1].lower() in FUNC else 0)
        if best is None or sc < best[0]: best = (sc, L, R)
    return split_long(best[1]) + split_long(best[2])

def chunks(txt):
    if '|' in txt: return [p.strip() for p in txt.split('|') if p.strip()]
    out = []
    for p in [p.strip() for p in re.split(r'(?<=[.!?:])\s+', txt) if p.strip()]: out += split_long(p)
    return out

# ------------------------------------------------------------ áudio
def lp(x, a):
    from scipy.signal import lfilter
    return lfilter([a], [1, a - 1], x)

def tone(freq, dur, det=0.0):
    t = np.arange(int(dur * SR)) / SR; f = freq * (1 + det); return 2 * ((f * t) % 1) - 1

def tts(falas, vozes):
    from kokoro_onnx import Kokoro
    k = Kokoro(f'{MODELOS}/kokoro-v1.0.onnx', f'{MODELOS}/voices-v1.0.bin')
    out = []
    for f in falas:
        voz, vel = vozes.get(f['quem'], vozes['narrador'])
        s, sr = k.create(f['texto'].replace('|', ''), voice=voz, speed=vel, lang='pt-br')
        s = np.asarray(s, np.float32); nz = np.where(np.abs(s) > .01)[0]; s = s[max(0, nz[0] - 200):nz[-1] + 2000]
        n = int(len(s) * SR / sr); s = np.interp(np.linspace(0, len(s) - 1, n), np.arange(len(s)), s).astype(np.float32)
        out.append(s / (np.abs(s).max() + 1e-6) * .9)
    return out

def trilha(total, humor='paz'):
    def note(m): return 440 * 2 ** ((m - 69) / 12)
    progs = {'paz': [[50, 57, 62, 66], [47, 54, 62, 66], [43, 55, 59, 62], [45, 52, 57, 61]],
             'tensao': [[50, 57, 62, 65], [46, 53, 62, 65], [53, 57, 60, 65], [48, 55, 60, 64]]}
    prog = progs.get(humor, progs['paz'])
    mus = np.zeros(int(total * SR) + SR); k = 0; tt = 0
    while tt < total:
        d = min(4.0, total - tt + .5)
        seg = sum(tone(note(m), d, det) * .04 for m in prog[k % 4] for det in (-.004, .005))
        seg = lp(seg, .02); n = len(seg)
        e = np.minimum(1, np.arange(n) / (SR * 1.5)) * np.minimum(1, (n - np.arange(n)) / (SR * 1.5))
        a = int(tt * SR); mus[a:a + n] += (seg * e)[:len(mus) - a]; tt += 4; k += 1
    for i in range(int(total / .5)):
        m = prog[(i // 8) % 4][i % 4] + 24; n = int(1.5 * SR); x = np.arange(n) / SR
        a = int(i * .5 * SR); mus[a:a + n] += (np.sin(2 * np.pi * note(m) * x) * np.exp(-x * 3) * .05)[:len(mus) - a]
    return mus[:int(total * SR)]

def chuva_som(total):
    rng = np.random.default_rng(5); n = int(total * SR)
    return lp(rng.standard_normal(n), .25) * .05

# ------------------------------------------------------------ efeitos visuais
class Chuva:
    def __init__(self, n=220, seed=2):
        r = random.Random(seed)
        self.g = [(r.uniform(0, W), r.uniform(0, H), r.uniform(900, 1500), r.uniform(30, 60)) for _ in range(n)]
    def draw(self, c, t):
        p = skia.Paint(AntiAlias=True, Color=skia.Color(220, 230, 255, 150), StrokeWidth=3, Style=skia.Paint.kStroke_Style)
        for x, y, v, L in self.g:
            yy = (y + t * v) % (H + 100) - 50; xx = (x - t * v * .15) % W
            c.drawLine(xx, yy, xx - L * .15, yy + L, p)

def overlay(c, cor, a):
    c.drawRect(skia.Rect(0, 0, W, H), skia.Paint(Color=skia.Color(*cor, int(a))))

def luz(c, t):
    c.save(); c.translate(W * .5, -100)
    for k in range(7):
        ang = -25 + k * 8 + math.sin(t * .4 + k) * 2
        c.save(); c.rotate(ang)
        p = skia.Path(); p.moveTo(-20, 0); p.lineTo(20, 0); p.lineTo(160, 2400); p.lineTo(-160, 2400); p.close()
        c.drawPath(p, skia.Paint(AntiAlias=True, Color=skia.Color(255, 250, 220, 28)))
        c.restore()
    c.restore()

# ------------------------------------------------------------ cache de arte
_img = {}
def img(nome):
    if nome not in _img: _img[nome] = skia.Image.open(f'{RAIZ}/arte/{nome}.png')
    return _img[nome]
_cut = {}
def recorte(nome):
    if nome not in _cut: _cut[nome] = to_skia(cutout(f'{RAIZ}/arte/{nome}.png'))
    return _cut[nome]
_pup = {}
def boneco(arte):
    if arte not in _pup: _pup[arte] = Puppet(f'{RAIZ}/arte/{arte}.png', RIGS.get(arte, {}))
    return _pup[arte]

def normalizar(R):
    """converte o formato antigo para o v2"""
    if 'cenas' in R: return R
    elenco = {n: dict(p) for n, p in R['personagens'].items()}
    atores = [dict(quem=n, x=p['x'], altura=p.get('altura', .55), olha=p.get('olha'), zoom=p.get('zoom', 1.25))
              for n, p in R['personagens'].items()]
    R = dict(R); R['elenco'] = elenco
    R['cenas'] = [dict(cenario=R['cenario'], atores=atores, falas=R['falas'])]
    return R

# ------------------------------------------------------------ desenho de uma cena
def desenhar_cena(c, cena, R, t, tl_cena, env_val, quem_fala, cam):
    bg = img(cena['cenario'])
    ef = cena.get('efeito', [])
    sway = math.sin(t * 1.6) * 10 if 'ondas' in ef else 0
    c.save(); c.translate(W / 2, H * .62); c.scale(cam['z'], cam['z']); c.translate(-cam['x'], -H * .62)
    s = H / bg.height() * 1.04
    c.save(); c.translate(W / 2, H / 2); c.scale(s, s)
    c.translate(-bg.width() / 2 + math.sin(t * .2) * 4, -bg.height() / 2 + (math.sin(t * .8) * 3 if 'ondas' in ef else 0))
    c.drawImage(bg, 0, 0, SAMP); c.restore()
    if 'luz' in ef: luz(c, t)
    # objetos (animais, arca, barco...)
    for o in cena.get('objetos', []):
        im = recorte(o['arte']); alt = o.get('altura', .25) * H; sc = alt / im.height()
        x = o.get('x', .5) * W; y = o.get('y', .8) * H; rot = 0
        an = o.get('anim', '')
        if an == 'flutua': y += math.sin(t * 1.5) * 12; rot = math.sin(t * 1.1) * 3
        if an == 'balanca': rot = math.sin(t * 1.6) * 6; y += math.sin(t * 1.6 + 1) * 8
        if an == 'nada': x += math.sin(t * .6) * 120; y += math.sin(t * 1.4) * 15; rot = math.sin(t * 1.4) * 5
        if an == 'voa':
            k = (t % 6) / 6; x = lerp(-.2 * W, 1.2 * W, k); y += math.sin(t * 6) * 18
        flip = o.get('olha') == 'esquerda'
        c.save(); c.translate(x, y); c.rotate(rot); c.scale(-sc if flip else sc, sc)
        c.drawImage(im, -im.width() / 2, -im.height(), SAMP); c.restore()
    # personagens
    for a in cena.get('atores', []):
        nome = a['quem']; el = R['elenco'][nome]; pup = boneco(el['arte'])
        alt = a.get('altura', .5) * H; esc = alt / pup.h
        x = a.get('x', .5) * W; y = H * a.get('chao', .87)
        bob = 0; flip = a.get('olha') == 'esquerda'
        ent = a.get('entra')
        if ent and t < 1.6:  # entra andando
            k = ease(clamp(t / 1.6)); x0 = -.25 * W if ent == 'esquerda' else 1.25 * W
            x = lerp(x0, x, k); bob = -abs(math.sin(t * 9)) * 14 * (1 - k)
            flip = ent == 'direita'
        if 'ondas' in ef: y += math.sin(t * 1.6 + x * .01) * 10
        falando = quem_fala == nome
        talk = env_val if falando else 0.0
        if falando and not (RIGS.get(el['arte']) or {}).get('mouth'):  # sem boca configurada: pulinho ao falar
            bob -= env_val * 10
        c.drawOval(skia.Rect(x - alt * .2, y - 24, x + alt * .2, y + 24), skia.Paint(AntiAlias=True,
                   Color=skia.Color(30, 40, 20, 60), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 14)))
        blink = ((t + hash(nome) % 7) % 3.4) > 3.25
        pup.draw(c, x, y + bob, esc, t + hash(nome) % 5, talk=talk, blink=blink, flip=flip)
    c.restore()
    if 'chuva' in ef: Chuva().draw(c, t)
    if 'noite' in ef: overlay(c, (10, 20, 60), 90)
    if 'relampago' in ef and (t % 5.3) < .12: overlay(c, (255, 255, 255), 170)

# ------------------------------------------------------------ principal
DRY = '--duracao' in sys.argv

def gerar(caminho, preview=False):
    R = normalizar(json.load(open(caminho, encoding='utf-8')))
    slug = os.path.splitext(os.path.basename(caminho))[0]
    elenco = R['elenco']
    vozes = {'narrador': (R.get('voz_narrador', 'pm_alex'), R.get('velocidade_narrador', .92))}
    for n, p in elenco.items(): vozes[n] = (p.get('voz', 'pm_santa'), p.get('velocidade', .9))
    falas = []; cena_de = []
    for i, cn in enumerate(R['cenas']):
        for f in cn['falas']: falas.append(f); cena_de.append(i)
    clips = tts(falas, vozes)

    # REGRA DE MONETIZAÇÃO (todas as plataformas): 95s a 170s.
    # TikTok paga só >1 min (regra do canal: 91s+ com margem); YouTube Shorts e Reels até 3 min.
    MIN = max(95.0, R.get('duracao_minima', 95.0)); MAX = 170.0
    est = .4 + sum(len(cl) / SR + f.get('pausa', .5) for f, cl in zip(falas, clips)) \
        + sum(c.get('respiro', .5) for c in R['cenas'][1:]) + 2.6
    print(f'duração estimada pela fala: {est:.1f}s (mínimo {MIN:.0f}s)')
    if est < MIN - 4:
        raise SystemExit(f'ROTEIRO CURTO: {est:.1f}s de conteúdo; precisa de pelo menos {MIN-4:.0f}s (sem encher de silêncio)')
    if est > MAX:
        raise SystemExit(f'ROTEIRO LONGO: {est:.1f}s; máximo {MAX:.0f}s')
    if DRY: return None, est
    falta = max(0.0, MIN + 2.5 - est); extra = min(.7, falta / max(1, len(falas))); falta -= extra * len(falas)
    t = .4; tl = []; inicio = {}; fim = {}
    for f, cl, ci in zip(falas, clips, cena_de):
        if ci not in inicio:
            inicio[ci] = max(0, t - .4)
            if ci > 0: t += R['cenas'][ci].get('respiro', .5)
        d = len(cl) / SR; cs = chunks(f['texto']); wts = [len(x) for x in cs]; tt = t; caps = []
        for x, w in zip(cs, wts): caps.append((tt, tt + d * w / sum(wts), x)); tt += d * w / sum(wts)
        tl.append(dict(quem=f['quem'], start=t, end=t + d, caps=caps, cena=ci)); t += d + f.get('pausa', .5) + extra
        fim[ci] = t
    CARD = 2.6 + max(0.0, falta); TOTAL = t + CARD
    ncenas = len(R['cenas'])
    lim = [inicio[i] for i in range(ncenas)] + [TOTAL]

    voice = np.zeros(int(TOTAL * SR) + SR)
    for seg, cl in zip(tl, clips): a = int(seg['start'] * SR); voice[a:a + len(cl)] += cl
    voice = voice[:int(TOTAL * SR)]
    hop = SR // FPS; nfr = int(TOTAL * FPS) + 1
    env = np.array([np.sqrt(np.mean(voice[i * hop:(i + 1) * hop] ** 2)) if i * hop < len(voice) else 0 for i in range(nfr)])
    env = np.convolve(np.clip(env / (env.max() * .6 + 1e-9), 0, 1), [.25, .5, .25], 'same')
    mus = trilha(TOTAL, R.get('trilha', 'paz'))
    ve = np.convolve(np.abs(voice), np.ones(SR // 10) / (SR // 10), 'same')
    mus = mus / (np.abs(mus).max() + 1e-9) * .35 * (1 - .5 * np.clip(ve * 12, 0, 1))
    amb = np.zeros_like(mus)
    for i, cn in enumerate(R['cenas']):
        if 'chuva' in cn.get('efeito', []):
            a, b = int(lim[i] * SR), min(int(lim[i + 1] * SR), len(amb)); ch = chuva_som((b - a) / SR + .05)[:b - a]; amb[a:a + len(ch)] += ch
    mix = np.tanh((voice * .95 + mus + amb) * 1.1) / np.tanh(1.1)
    mix *= np.minimum(1, (len(mix) - np.arange(len(mix))) / (SR * 1.2))
    os.makedirs(f'{RAIZ}/videos', exist_ok=True)
    wav = f'/tmp/{slug}.wav'; sf.write(wav, np.stack([mix, mix], 1).astype(np.float32), SR)

    fcap = font('Cormorant-Bold', 88); ftit = font('Cinzel-Bold', 84); fsub = font('Cormorant-Bold', 52)
    dust = Dust(40, 3, '#fff6d0')
    ow, oh = (540, 960) if preview else (W, H)
    out = f"{RAIZ}/videos/{slug}{'-preview' if preview else ''}.mp4"
    ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'bgra', '-s', f'{W}x{H}', '-r', str(FPS),
                           '-i', '-', '-i', wav, '-vf', f'scale={ow}:{oh}:flags=lanczos', '-c:v', 'libx264', '-preset', 'veryfast',
                           '-crf', '18', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', out],
                          stdin=subprocess.PIPE)
    surf = skia.Surface(W, H); tmp = skia.Surface(W, H)
    cams = [dict(z=1.0, x=W / 2) for _ in range(ncenas)]
    def fala_em(t):
        for s in tl:
            if s['start'] - .05 <= t <= s['end'] + .05: return s['quem']
        return None
    XF = .45
    for fr in range(int(TOTAL * FPS)):
        t = fr / FPS; c = surf.getCanvas(); c.clear(skia.ColorWHITE)
        ci = max(i for i in range(ncenas) if lim[i] <= t + 1e-9)
        quem = fala_em(t)
        cena = R['cenas'][ci]
        alvo_z, alvo_x = 1.0, W / 2
        for a in cena.get('atores', []):
            if a['quem'] == quem: alvo_z, alvo_x = a.get('zoom', 1.18), a.get('x', .5) * W
        cam = cams[ci]
        if t - lim[ci] < 1 / FPS: cam.update(z=alvo_z * .97 if alvo_z > 1 else 1.0, x=alvo_x)
        cam['z'] += (alvo_z - cam['z']) * .035; cam['x'] += (alvo_x - cam['x']) * .035
        ev = float(env[min(fr, len(env) - 1)])
        desenhar_cena(c, cena, R, t - lim[ci], None, ev, quem, cam)
        if ci > 0 and t - lim[ci] < XF:  # transição: a cena anterior some aos poucos
            tc = tmp.getCanvas(); tc.clear(skia.ColorWHITE)
            desenhar_cena(tc, R['cenas'][ci - 1], R, t - lim[ci - 1], None, 0, None, cams[ci - 1])
            a = 1 - ease((t - lim[ci]) / XF)
            c.drawImage(tmp.makeImageSnapshot(), 0, 0, SAMP, skia.Paint(Alphaf=a))
        dust.draw(c, t, .5, wind=8)
        atual = None
        for seg in tl:
            for a, b, txt in seg['caps']:
                if a <= t <= b + .25: atual = (a, b, txt, seg['quem'])
        if atual:
            a, b, txt, q = atual
            al = int(255 * min(clamp((t - a) / .12), clamp((b + .25 - t) / .15)))
            col = elenco.get(q, {}).get('cor', '#ffffff'); ls = wrap(txt)
            for k, ln in enumerate(ls):
                text_center(c, ln, H * .115 + (k - (len(ls) - 1) / 2) * 96, fcap, col, al, outline='#4a2412')
        if t > TOTAL - CARD:
            a = ease(clamp((t - (TOTAL - CARD)) / .6))
            c.drawRect(skia.Rect(0, 0, W, H), skia.Paint(Color=skia.Color(40, 18, 6, int(150 * a))))
            text_center(c, R.get('referencia', '').upper(), H * .42, ftit, '#fff3cf', int(255 * a), outline='#4a2412')
            text_center(c, 'Siga o Dádiva dos Céus', H * .42 + 100, fsub, '#ffffff', int(255 * a), outline='#4a2412')
        if fr < 8: overlay(c, (0, 0, 0), 255 * (1 - fr / 8))
        ff.stdin.write(surf.makeImageSnapshot().tobytes())
    ff.stdin.close(); ff.wait()
    real = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', out],
                                capture_output=True, text=True).stdout)
    if not (MIN <= real <= MAX + 3):
        os.replace(out, out + '.INVALIDO'); raise SystemExit(f'VÍDEO FORA DA REGRA: {real:.1f}s')
    print(f'pronto: {out} ({real:.1f}s, dentro da regra 95-170s)')
    return out, real

if __name__ == '__main__':
    gerar(sys.argv[1], '--preview' in sys.argv)
