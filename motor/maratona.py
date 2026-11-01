"""Maratona horizontal: junta Shorts (verticais) com pontes narradas.
Uso: python motor/maratona.py leituras/roteiros/maratona-1.txt
Saída: videos-longos/<slug>.mp4 (1920x1080, 30 fps)
"""
import os, sys, json, subprocess, glob
import numpy as np, cv2, skia, soundfile as sf
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from leitura import falar, fonte, SR
from episodio import trilha

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W, H, FPS = 1920, 1080, 30
TMP = '/tmp/maratona'

def run(cmd): subprocess.run(cmd, check=True)

def fim_util(video):
    """Instante em que começa o cartão final do Short (para cortar)."""
    cap = cv2.VideoCapture(video); n = cap.get(cv2.CAP_PROP_FRAME_COUNT); fps = cap.get(cv2.CAP_PROP_FPS)
    def fr(t):
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(t * fps)); ok, f = cap.read()
        return cv2.resize(f, (108, 192)).astype(np.float32) if ok else None
    dur = n / fps; ult = fr(dur - .2); t = dur - .2
    while t > dur - 20:
        f = fr(t - .25)
        if f is None or np.abs(f - ult).mean() > 6: break
        t -= .25
    return max(1, t - .7)

def titulo_short(slug):
    R = json.load(open(f'{RAIZ}/roteiros/{slug}.json')); return R['titulo'].split(' ')[0:], R
def quadro_fundo(video, t=3.0):
    cap = cv2.VideoCapture(video); cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000); ok, f = cap.read(); return f

def cartao(fundo_bgr, linhas, saida):
    bg = cv2.resize(fundo_bgr, (W, int(W * fundo_bgr.shape[0] / fundo_bgr.shape[1])))
    y0 = (bg.shape[0] - H) // 2; bg = bg[y0:y0 + H]
    bg = cv2.GaussianBlur(bg, (0, 0), 28); bg = (bg * .55).astype(np.uint8)
    rgba = cv2.cvtColor(bg, cv2.COLOR_BGR2RGBA); s = skia.Surface(rgba)
    with s as c:
        y = H * .42 - (len(linhas) - 1) * 50
        for txt, fn, tam, cor in linhas:
            f = fonte(fn, tam); w = f.measureText(txt)
            c.drawString(txt, W / 2 - w / 2 + 3, y + 4, f, skia.Paint(AntiAlias=True, Color=skia.Color(0, 0, 0, 170), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 8)))
            c.drawString(txt, W / 2 - w / 2, y, f, skia.Paint(AntiAlias=True, Color=skia.Color(*cor)))
            y += tam * 1.25 + 28
    cv2.imwrite(saida, cv2.cvtColor(rgba, cv2.COLOR_RGBA2BGR))

def ponte_mp4(png, voz, saida, extra=1.2):
    if os.path.exists(saida): return
    d = len(voz) / SR + extra + .6
    mus = trilha(d + 1, 'paz')[:int(d * SR)] * .35
    a = np.zeros(int(d * SR), np.float32); i = int(.6 * SR); a[i:i + len(voz)] += voz
    a[:len(mus)] += mus; a = a / (np.abs(a).max() + 1e-6) * .85
    fo = int(.6 * SR); a[-fo:] *= np.linspace(1, 0, fo)
    sf.write(saida + '.wav', a, SR)
    tmp = saida + '.tmp.mp4'
    run(['ffmpeg', '-y', '-loglevel', 'error', '-loop', '1', '-framerate', str(FPS), '-i', png, '-i', saida + '.wav',
         '-vf', f"zoompan=z='min(1.0+on/{FPS}*0.004,1.08)':d=1:s={W}x{H}:fps={FPS},fade=t=in:st=0:d=0.5,fade=t=out:st={d-.6:.2f}:d=0.6",
         '-t', f'{d:.2f}', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '20', '-pix_fmt', 'yuv420p',
         '-c:a', 'aac', '-b:a', '160k', '-ar', '44100', '-ac', '2', tmp]); os.replace(tmp, saida)

def short_mp4(video, saida):
    if os.path.exists(saida): return
    t = fim_util(video)
    fc = (f"[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},boxblur=30:3,eq=brightness=-0.18[bg];"
          f"[0:v]scale=-2:1000[fg];[bg][fg]overlay=(W-w)/2:40,fade=t=in:st=0:d=0.4,fade=t=out:st={t-.5:.2f}:d=0.5[v]")
    run(['ffmpeg', '-y', '-loglevel', 'error', '-i', video, '-t', f'{t:.2f}', '-filter_complex', fc, '-map', '[v]', '-map', '0:a',
         '-af', f'afade=t=out:st={t-.5:.2f}:d=0.5', '-r', str(FPS), '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '20',
         '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '160k', '-ar', '44100', '-ac', '2', saida + '.tmp.mp4']); os.replace(saida + '.tmp.mp4', saida)

def gerar(caminho):
    slug = os.path.splitext(os.path.basename(caminho))[0]; os.makedirs(TMP, exist_ok=True)
    L = open(caminho, encoding='utf-8').read().split('\n')
    titulo, sub = [x.strip() for x in L[0].lstrip('# ').split('|')]
    partes = []; atual = None
    for ln in L[1:]:
        if ln.startswith('@'): atual = [ln[1:].strip(), []]; partes.append(atual)
        elif ln.strip(): atual[1].append(ln.strip())
    import pickle, hashlib
    txs = [' '.join(p[1]) for p in partes]
    ck = f"{TMP}/tts_{hashlib.md5(json.dumps(txs).encode()).hexdigest()}.pkl"
    if os.path.exists(ck): vozes = pickle.load(open(ck, 'rb'))
    else: vozes = falar(txs, 'pm_santa', 1.0); pickle.dump(vozes, open(ck, 'wb'))
    lista = []; n = 0
    for (chave, _), voz in zip(partes, vozes):
        if chave in ('abertura', 'encerramento'):
            fundo = quadro_fundo(f'{RAIZ}/videos/003-noe-e-a-arca.mp4' if chave == 'abertura' else f'{RAIZ}/videos/015-venham-a-mim.mp4')
            linhas = [(titulo.upper(), 'Cinzel-Bold', 84, (255, 240, 205, 255)), (sub, 'Cormorant-Medium', 54, (255, 250, 240, 255))] if chave == 'abertura' else \
                     [('Dádiva dos Céus', 'Cinzel-Bold', 84, (255, 240, 205, 255)), ('Inscreva-se e até a próxima maratona!', 'Cormorant-Medium', 54, (255, 250, 240, 255))]
            png = f'{TMP}/{chave}.png'; cartao(fundo, linhas, png)
            out = f'{TMP}/{len(lista):02d}_{chave}.mp4'; ponte_mp4(png, voz, out, extra=2.0 if chave == 'encerramento' else 1.2); lista.append(out)
            continue
        n += 1; R = json.load(open(f'{RAIZ}/roteiros/{chave}.json')); vid = f'{RAIZ}/videos/{chave}.mp4'
        import re as _re
        nome = _re.split(r'[^\w\s,.:;!?\-áéíóúâêôãõçÁÉÍÓÚÂÊÔÃÕÇ]', R['titulo'])[0].strip()
        linhas = [(f'HISTÓRIA {n}', 'Cinzel', 40, (240, 200, 120, 255)), (nome, 'Cinzel-Bold', 64, (255, 240, 205, 255)),
                  (R.get('referencia', ''), 'Cormorant-Medium', 46, (235, 225, 205, 255))]
        png = f'{TMP}/p{n:02d}.png'; cartao(quadro_fundo(vid), linhas, png)
        out = f'{TMP}/{len(lista):02d}_ponte_{n:02d}.mp4'; ponte_mp4(png, voz, out); lista.append(out)
        out = f'{TMP}/{len(lista):02d}_short_{n:02d}.mp4'; short_mp4(vid, out); lista.append(out)
        print('ok', n, chave, flush=True)
    open(f'{TMP}/lista.txt', 'w').write(''.join(f"file '{x}'\n" for x in lista))
    final = f'{RAIZ}/videos-longos/{slug}.mp4'
    run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', f'{TMP}/lista.txt', '-c:v', 'libx264', '-preset', 'veryfast',
         '-crf', '20', '-pix_fmt', 'yuv420p', '-r', str(FPS), '-c:a', 'aac', '-b:a', '160k', '-ar', '44100', '-ac', '2', '-movflags', '+faststart', final])
    print('ok', final)
    # trava de segurança: nada sai sem passar na checagem (áudio mudo, tela preta)
    run([sys.executable, f'{RAIZ}/motor/checar_video.py', final])

if __name__ == '__main__':
    gerar(sys.argv[1])
