"""Capa 1080x1920 para Short: quadro do vídeo + faixa no topo com o título (cobre a legenda).
Uso: python motor/capa_short.py <video.mp4> "<Título>" "<subtítulo>" <saida.jpg> [segundo]"""
import sys, os, subprocess, cv2, numpy as np, skia
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
v, tit, sub, out = sys.argv[1:5]; seg = sys.argv[5] if len(sys.argv) > 5 else '3'
subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-ss', seg, '-i', v, '-frames:v', '1', '/tmp/_capa.png'], check=True)
img = cv2.imread('/tmp/_capa.png'); H, W = img.shape[:2]
y = np.arange(H, dtype=np.float32)[:, None, None]
k = np.clip(1 - (y - 640) / 240, 0, 1) * (y < 880); img = (img * (1 - k) + np.array([10, 22, 48], np.float32) * k).astype(np.uint8)  # faixa escura no topo (esconde a legenda)
rgba = cv2.cvtColor(img, cv2.COLOR_BGR2RGBA); s = skia.Surface(rgba)
F = lambda n, t: skia.Font(skia.Typeface.MakeFromFile(f'{RAIZ}/fontes/{n}.ttf'), t)
def centro(c, t, yy, f, cor, borda=10):
    x = (W - f.measureText(t)) / 2
    c.drawString(t, x, yy, f, skia.Paint(AntiAlias=True, Color=skia.Color(40, 18, 6), Style=skia.Paint.kStroke_Style, StrokeWidth=borda, StrokeJoin=skia.Paint.kRound_Join))
    c.drawString(t, x, yy, f, skia.Paint(AntiAlias=True, Color=cor))
def linhas(t, f, maxw):
    ws, ls, cur = t.split(), [], ''
    for w in ws:
        if f.measureText((cur + ' ' + w).strip()) <= maxw: cur = (cur + ' ' + w).strip()
        else: ls.append(cur); cur = w
    return ls + [cur]
with s as c:
    tam = 128; f = F('Cinzel-Bold', tam)
    while len(linhas(tit.upper(), f, 980)) > 2 or max(f.measureText(l) for l in linhas(tit.upper(), f, 980)) > 980: tam -= 6; f = F('Cinzel-Bold', tam)
    ls = linhas(tit.upper(), f, 980); y0 = 470 if len(ls) == 1 else 420  # dentro do recorte 3:4 da grade do Instagram
    for i, l in enumerate(ls): centro(c, l, y0 + i * tam * 1.05, f, skia.Color(255, 240, 200))
    fs = F('Cormorant-Bold', 66); ys = y0 + len(ls) * tam * 1.05 + 30
    for i, l in enumerate(linhas(sub, fs, 960)): centro(c, l, ys + i * 72, fs, skia.Color(255, 255, 255), 8)
cv2.imwrite(out, cv2.cvtColor(rgba, cv2.COLOR_RGBA2BGR), [cv2.IMWRITE_JPEG_QUALITY, 90])
