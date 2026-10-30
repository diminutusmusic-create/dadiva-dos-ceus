"""Gera um episódio a partir de um roteiro JSON.
Uso: python motor/episodio.py roteiros/001-vinde-a-mim.json [--preview]
Saída: videos/<slug>.mp4 (1080x1920, 30 fps)
"""
import json, math, os, re, subprocess, sys
import numpy as np, soundfile as sf
import skia
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from engine import W, H, FPS, font, text_center, ease, clamp, lerp, Dust
from cartoon_rig import Puppet, RIGS

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SR = 44100
MODELOS = os.environ.get('KOKORO_DIR', f'{RAIZ}/modelos')

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
        voz, vel = vozes[f['quem']]
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
    for i in range(int(total / .5)):  # arpejo de harpa
        m = prog[(i // 8) % 4][i % 4] + 24; n = int(1.5 * SR); x = np.arange(n) / SR
        a = int(i * .5 * SR); mus[a:a + n] += (np.sin(2 * np.pi * note(m) * x) * np.exp(-x * 3) * .05)[:len(mus) - a]
    return mus[:int(total * SR)]

# ------------------------------------------------------------ principal
def gerar(caminho, preview=False):
    R = json.load(open(caminho, encoding='utf-8'))
    slug = os.path.splitext(os.path.basename(caminho))[0]
    pers = R['personagens']
    vozes = {'narrador': (R.get('voz_narrador', 'pm_alex'), R.get('velocidade_narrador', .92))}
    for nome, p in pers.items(): vozes[nome] = (p.get('voz', 'pm_santa'), p.get('velocidade', .92))
    falas = R['falas']
    clips = tts(falas, vozes)

    GAP = .45; t = .4; tl = []
    for f, cl in zip(falas, clips):
        d = len(cl) / SR; cs = chunks(f['texto']); wts = [len(x) for x in cs]; tt = t; caps = []
        for x, w in zip(cs, wts): caps.append((tt, tt + d * w / sum(wts), x)); tt += d * w / sum(wts)
        tl.append(dict(quem=f['quem'], start=t, end=t + d, caps=caps)); t += d + f.get('pausa', GAP)
    CARD = 2.6; TOTAL = t + CARD

    voice = np.zeros(int(TOTAL * SR) + SR)
    for seg, cl in zip(tl, clips): a = int(seg['start'] * SR); voice[a:a + len(cl)] += cl
    voice = voice[:int(TOTAL * SR)]
    hop = SR // FPS; nfr = int(TOTAL * FPS) + 1
    env = np.array([np.sqrt(np.mean(voice[i * hop:(i + 1) * hop] ** 2)) if i * hop < len(voice) else 0 for i in range(nfr)])
    env = np.convolve(np.clip(env / (env.max() * .6 + 1e-9), 0, 1), [.25, .5, .25], 'same')
    mus = trilha(TOTAL, R.get('trilha', 'paz'))
    ve = np.convolve(np.abs(voice), np.ones(SR // 10) / (SR // 10), 'same')
    mus = mus / (np.abs(mus).max() + 1e-9) * .35 * (1 - .5 * np.clip(ve * 12, 0, 1))
    mix = np.tanh((voice * .95 + mus) * 1.1) / np.tanh(1.1)
    mix *= np.minimum(1, (len(mix) - np.arange(len(mix))) / (SR * 1.2))
    os.makedirs(f'{RAIZ}/videos', exist_ok=True)
    wav = f'/tmp/{slug}.wav'; sf.write(wav, np.stack([mix, mix], 1).astype(np.float32), SR)

    bg = skia.Image.open(f"{RAIZ}/arte/{R['cenario']}.png")
    bonecos = {n: Puppet(f"{RAIZ}/arte/{p['arte']}.png", RIGS.get(p['arte'], {})) for n, p in pers.items()}
    samp = skia.SamplingOptions(skia.FilterMode.kLinear, skia.MipmapMode.kLinear)
    fcap = font('Cormorant-Bold', 88); ftit = font('Cinzel-Bold', 84); fsub = font('Cormorant-Bold', 52)
    dust = Dust(40, 3, '#fff6d0')
    ow, oh = (540, 960) if preview else (W, H)
    out = f"{RAIZ}/videos/{slug}{'-preview' if preview else ''}.mp4"
    ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'bgra', '-s', f'{W}x{H}', '-r', str(FPS),
                           '-i', '-', '-i', wav, '-vf', f'scale={ow}:{oh}:flags=lanczos', '-c:v', 'libx264', '-preset', 'veryfast',
                           '-crf', '18', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', out],
                          stdin=subprocess.PIPE)
    surf = skia.Surface(W, H)
    def falando(t):
        for s in tl:
            if s['start'] - .05 <= t <= s['end'] + .05: return s['quem']
        return None
    zoom_s = 1.0; foco_s = W / 2
    for fr in range(int(TOTAL * FPS)):
        t = fr / FPS; c = surf.getCanvas(); c.clear(skia.ColorWHITE)
        quem = falando(t)
        alvo_z, alvo_x = 1.0, W / 2
        if quem in pers: alvo_z, alvo_x = pers[quem].get('zoom', 1.25), pers[quem]['x'] * W
        zoom_s += (alvo_z - zoom_s) * .04; foco_s += (alvo_x - foco_s) * .04
        c.save(); c.translate(W / 2, H * .62); c.scale(zoom_s, zoom_s); c.translate(-foco_s, -H * .62)
        s = H / bg.height() * 1.04
        c.save(); c.translate(W / 2, H / 2); c.scale(s, s); c.translate(-bg.width() / 2 + math.sin(t * .2) * 4, -bg.height() / 2)
        c.drawImage(bg, 0, 0, samp); c.restore()
        for nome, p in pers.items():
            x = p['x'] * W; y = H * p.get('chao', .87); alt = p.get('altura', .55) * H
            esc = alt / bonecos[nome].h
            c.drawOval(skia.Rect(x - alt * .2, y - 24, x + alt * .2, y + 24), skia.Paint(AntiAlias=True, Color=skia.Color(30, 60, 20, 70),
                       MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 14)))
            talk = float(env[min(fr, len(env) - 1)]) if quem == nome else 0.0
            blink = ((t + hash(nome) % 7) % 3.4) > 3.25
            bonecos[nome].draw(c, x, y, esc, t + hash(nome) % 5, talk=talk, blink=blink, flip=p.get('olha') == 'esquerda')
        c.restore()
        dust.draw(c, t, .6, wind=8)
        atual = None
        for seg in tl:
            for a, b, txt in seg['caps']:
                if a <= t <= b + .25: atual = (a, b, txt, seg['quem'])
        if atual:
            a, b, txt, q = atual
            al = int(255 * min(clamp((t - a) / .12), clamp((b + .25 - t) / .15)))
            col = pers.get(q, {}).get('cor', '#ffffff'); ls = wrap(txt)
            for k, ln in enumerate(ls):
                text_center(c, ln, H * .115 + (k - (len(ls) - 1) / 2) * 96, fcap, col, al, outline='#4a2412')
        if t > TOTAL - CARD:  # cartão final
            a = ease(clamp((t - (TOTAL - CARD)) / .6))
            c.drawRect(skia.Rect(0, 0, W, H), skia.Paint(Color=skia.Color(40, 18, 6, int(150 * a))))
            text_center(c, R.get('referencia', '').upper(), H * .42, ftit, '#fff3cf', int(255 * a), outline='#4a2412')
            text_center(c, 'Siga o Dádiva dos Céus', H * .42 + 100, fsub, '#ffffff', int(255 * a), outline='#4a2412')
        if fr < 8: c.drawRect(skia.Rect(0, 0, W, H), skia.Paint(Color=skia.Color(0, 0, 0, int(255 * (1 - fr / 8)))))
        ff.stdin.write(surf.makeImageSnapshot().tobytes())
    ff.stdin.close(); ff.wait()
    print(f'pronto: {out} ({TOTAL:.1f}s)')
    return out, TOTAL

if __name__ == '__main__':
    gerar(sys.argv[1], '--preview' in sys.argv)
