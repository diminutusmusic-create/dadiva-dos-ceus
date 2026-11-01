"""Vídeos longos de louvor: abertura narrada + faixas do Treblo, cada uma sobre uma paisagem 2.5D,
com título, referência e versículo na tela no início de cada faixa. Render rápido: cada paisagem vira
um laço ida-e-volta (pingue-pongue) concatenado sem recodificar.
Uso: python motor/louvor.py louvores/<slug>.json
JSON: {"titulo","subtitulo","abertura": "texto narrado", "fechamento": "texto narrado",
       "faixas": [{"arquivo","titulo","ref","versiculo","cenario","efeito":[...]}]}
"""
import json, os, sys, subprocess, glob, math
import numpy as np, cv2, skia, soundfile as sf
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import leitura as L
from leitura import Cena, Nevoa, Poeira, Estrelas, vinheta, grade, fonte, centro, quebra, falar, ambiente

RAIZ = L.RAIZ; W, H = L.W, L.H
FPS = 24; SRM = 48000; LOOP = float(os.environ.get("LOOP", 40)); HEAD = float(os.environ.get("HEAD", 14)); GAP = 2.5

def rs(x, a, b):  # reamostragem linear
    n = int(len(x) * b / a); return np.interp(np.linspace(0, len(x) - 1, n), np.arange(len(x)), x).astype(np.float32)

def enc(path, nfr, gen):
    p = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{W}x{H}',
                          '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '21',
                          '-pix_fmt', 'yuv420p', '-g', str(FPS * 2), path + '.tmp.mp4'], stdin=subprocess.PIPE)
    for i in range(nfr): p.stdin.write(gen(i).tobytes())
    p.stdin.close(); p.wait(); os.replace(path + '.tmp.mp4', path)

def gerar(caminho):
    R = json.load(open(caminho, encoding='utf-8')); slug = os.path.splitext(os.path.basename(caminho))[0]
    T = f'/tmp/louvor_{slug}'; os.makedirs(T, exist_ok=True)
    ft, fsub, fref, fver, fm = (fonte('Cinzel-Bold', 92), fonte('Cormorant-Medium', 52), fonte('Cinzel', 34),
                                fonte('Cormorant-Medium', 50), fonte('Cinzel', 30))
    vin = vinheta(); nev = Nevoa(); poe = Poeira(); est = Estrelas()
    yy = np.arange(H, dtype=np.float32)[:, None, None]
    BANDA = np.exp(-((yy - H * .48) / (H * .16)) ** 2)  # faixa escurecida atrás do texto

    # ---------------- áudio
    nar = falar([R['abertura'], R.get('fechamento', 'Que a paz de Deus guarde o seu coração. Boa noite.')],
                R.get('voz', 'pm_santa'), R.get('velocidade', 1.0))
    nar = [rs(n, L.SR, SRM) for n in nar]
    musicas = []
    for f in R['faixas']:
        x, sr = sf.read(f['arquivo'], dtype='float32')
        x = x if x.ndim > 1 else np.stack([x, x], 1)
        if sr != SRM: x = np.stack([rs(x[:, c], sr, SRM).astype(np.float32) for c in range(2)], 1)
        x = x / (np.sqrt(np.mean(x ** 2)) + 1e-9) * .12          # mesmo volume percebido entre faixas
        fade = int(SRM * 1.5); x[-fade:] *= np.linspace(1, 0, fade)[:, None]
        musicas.append(x)
    abertura_d = 2.0 + len(nar[0]) / SRM + 2.0
    partes = [('abertura', abertura_d)]
    for i, m in enumerate(musicas): partes.append((f'faixa{i}', GAP + len(m) / SRM))
    fim_d = 1.5 + len(nar[1]) / SRM + 5.0
    partes.append(('fim', fim_d))
    total = sum(d for _, d in partes)
    mix = np.zeros((int(total * SRM) + SRM, 2), np.float32)
    t = 0.0
    for (nome, d) in partes:
        a = int(t * SRM)
        if nome == 'abertura': mix[a + 2 * SRM: a + 2 * SRM + len(nar[0])] += nar[0][:, None] * .9
        elif nome == 'fim': mix[a + int(1.5 * SRM): a + int(1.5 * SRM) + len(nar[1])] += nar[1][:, None] * .9
        else:
            m = musicas[int(nome[5:])]; b = a + int(GAP * SRM); mix[b:b + len(m)] += m
        t += d
    durs = [len(m) for m in musicas]; del musicas   # libera memória (vídeos de 1h)
    # ambiente: bloco de 120 s repetido com crossfade (gerar 1 h de uma vez estoura a memória)
    blk = rs(ambiente('riacho', 122), L.SR, SRM) * .6; X = SRM * 2; per = len(blk) - X
    rampa = np.linspace(0, 1, X, dtype=np.float32)
    lp_ = blk.copy(); lp_[:X] = blk[:X] * rampa + blk[-X:] * (1 - rampa); lp_ = lp_[:per]
    for a in range(0, len(mix), per):
        seg = lp_[:len(mix) - a]; mix[a:a + len(seg)] += seg[:, None]
    del blk, lp_
    k = np.float32(1 / np.tanh(1.1))
    for a in range(0, len(mix), SRM * 60):   # limitador em blocos, sem cópias grandes
        blk = mix[a:a + SRM * 60]; blk *= 1.1; np.tanh(blk, out=blk); blk *= k
    wav = f'{T}/audio.wav'; sf.write(wav, mix[:int(total * SRM)], SRM)

    # ---------------- vídeo
    def base(cena, tt, efs, g=1.0, texto=0.0):
        f = cena.frame(tt).astype(np.float32)
        if 'nevoa' in efs: f = nev.aplica(f, tt)
        f = grade(f) * vin * g
        if texto > 0: f = f * (1 - .5 * texto * BANDA)
        f = np.clip(f, 0, 255).astype(np.uint8)
        return cv2.cvtColor(f, cv2.COLOR_BGR2RGBA)
    def fecha(rgba): return cv2.cvtColor(rgba, cv2.COLOR_RGBA2BGR)
    def deco(c, tt, efs, g):
        if 'estrelas' in efs: est.draw(c, tt, g)
        if 'poeira' in efs or 'luz' in efs: poe.draw(c, tt, g)

    lista = []
    # abertura
    cen0 = R.get('cenario_abertura', R['faixas'][0]['cenario'])
    p = f'{T}/v_abertura.mp4'
    if not os.path.exists(p):
        c0 = Cena(cen0); n = int(abertura_d * FPS)
        def g_ab(i):
            tt = i / FPS; g = min(1, tt / 2.5, (abertura_d - tt) / 1.2)
            at = max(0, min(1, (tt - .8) / 1.5, (abertura_d - 1.5 - tt) / 1.5))
            rgba = base(c0, tt, ['nevoa'], max(g, 0), at)
            with skia.Surface(rgba) as c:
                deco(c, tt, ['poeira'], g)
                a = min(1, (tt - .8) / 1.5, (abertura_d - 1.5 - tt) / 1.5)
                if a > 0:
                    centro(c, R['titulo'], H * .44, ft, (255, 244, 220), a)
                    centro(c, R.get('subtitulo', ''), H * .44 + 78, fsub, (240, 220, 175), a)
            return fecha(rgba)
        enc(p, n, g_ab)
    lista.append((p, abertura_d))
    # faixas
    for i, f in enumerate(R['faixas']):
        d = GAP + durs[i] / SRM; efs = f.get('efeito', ['nevoa'])
        cena = None
        def C():
            nonlocal cena
            if cena is None: cena = Cena(f['cenario'])
            return cena
        ph, pt, pf, pr = (f'{T}/v{i:02d}_{k}.mp4' for k in ('head', 'tail', 'fwd', 'rev'))
        linhas_v = None
        if not os.path.exists(ph):
            pal = f['versiculo'].split(); linhas_v = [' '.join(pal[j] for j in l) for l in quebra(pal, fver, W * .62)]
            def g_h(k):
                tt = k / FPS; g = min(1, tt / 1.5)
                a = max(0, min(1, (tt - GAP) / 1.5, (HEAD - .5 - tt) / 1.5))
                rgba = base(C(), tt, efs, g, a)
                with skia.Surface(rgba) as c:
                    deco(c, tt, efs, g)
                    a = min(1, (tt - GAP) / 1.5, (HEAD - .5 - tt) / 1.5)
                    if a > 0:
                        centro(c, f['titulo'], H * .40, ft, (255, 244, 220), a)
                        centro(c, f['ref'], H * .40 + 62, fref, (230, 205, 150), a * .9)
                        y = H * .40 + 150
                        for ln in linhas_v: centro(c, ln, y, fver, (245, 236, 215), a * .95); y += 62
                    m = min(1, max(0, (tt - GAP - 1) / 1.5))
                    centro(c, f"{i + 1}. {f['titulo']}", H * .955, fm, (230, 205, 150), .55 * m)
                return fecha(rgba)
            enc(ph, int(HEAD * FPS), g_h)
        def g_plain(t0, sgn):
            def g(k):
                tt = t0 + sgn * k / FPS
                rgba = base(C(), tt, efs)
                with skia.Surface(rgba) as c:
                    deco(c, tt, efs, 1)
                    centro(c, f"{i + 1}. {f['titulo']}", H * .955, fm, (230, 205, 150), .55)
                return fecha(rgba)
            return g
        if not os.path.exists(pt): enc(pt, int((LOOP - HEAD) * FPS), g_plain(HEAD, 1))
        if not os.path.exists(pr): enc(pr, int(LOOP * FPS), g_plain(LOOP, -1))
        if not os.path.exists(pf): enc(pf, int(LOOP * FPS), g_plain(0, 1))
        seq = [ph, pt]; acc = LOOP; k = 0
        while acc < d: seq.append(pr if k % 2 == 0 else pf); acc += LOOP; k += 1
        open(f'{T}/l{i:02d}.txt', 'w').write(''.join(f"file '{x}'\n" for x in seq))
        pi = f'{T}/faixa{i:02d}.mp4'
        if not os.path.exists(pi):
            subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', f'{T}/l{i:02d}.txt',
                            '-t', f'{d:.3f}', '-c', 'copy', pi], check=True)
        lista.append((pi, d)); print('faixa', i, f['titulo'], f'{d:.0f}s', flush=True)
    # fim
    p = f'{T}/v_fim.mp4'
    if not os.path.exists(p):
        cf = Cena(R.get('cenario_fim', 'casa_noite'))
        def g_f(k):
            tt = k / FPS; g = min(1, tt / 1.5, (fim_d - tt) / 3)
            af = max(0, min(1, (tt - fim_d + 6) / 1.5, (fim_d - tt) / 1.5))
            rgba = base(cf, tt, ['estrelas'], max(g, 0), af)
            with skia.Surface(rgba) as c:
                deco(c, tt, ['estrelas'], g)
                a = min(1, (tt - fim_d + 6) / 1.5, (fim_d - tt) / 1.5)
                if a > 0:
                    centro(c, 'Dádiva dos Céus', H * .46, ft, (255, 244, 220), a)
                    centro(c, 'Louvores com letras originais inspiradas nas Escrituras', H * .46 + 70, fm, (230, 205, 150), a * .8)
            return fecha(rgba)
        enc(p, int(fim_d * FPS), g_f)
    lista.append((p, fim_d))
    open(f'{T}/lista.txt', 'w').write(''.join(f"file '{x}'\n" for x, _ in lista))
    out = f'{RAIZ}/videos-longos/{slug}.mp4'
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', f'{T}/lista.txt', '-i', wav,
                    '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', out], check=True)
    # capítulos para a descrição
    t = 0; cap = []
    for (nome, d) in partes:
        if nome == 'abertura': cap.append((0, 'Abertura e oração'))
        elif nome.startswith('faixa'): cap.append((t + GAP, R['faixas'][int(nome[5:])]['titulo']))
        elif nome == 'fim': cap.append((t, 'Oração final'))
        t += d
    fmt = lambda s: f'{int(s // 3600)}:{int(s % 3600 // 60):02d}:{int(s % 60):02d}' if s >= 3600 else f'{int(s // 60)}:{int(s % 60):02d}'
    json.dump([[fmt(s), n] for s, n in cap], open(f'{RAIZ}/louvores/{slug}.capitulos.json', 'w'), ensure_ascii=False)
    print('ok', out, f'{total:.0f}s')

if __name__ == '__main__':
    gerar(sys.argv[1])
