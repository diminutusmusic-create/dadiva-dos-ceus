"""Capa padrão dos vídeos longos (2560x1440), no estilo aprovado:
azul-noite texturizado, título central "SALMO 91", linha com estrela, promessa dourada,
colinas em camadas embaixo e um objeto dourado luminoso no centro."""
import sys, math, os, numpy as np, cv2, skia
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import marca_v4 as M
W, H = 2560, 1440
T = M.TEMAS['solido']
CREME = skia.Color(250, 243, 226)
def ouro_grad(y0, y1): return skia.GradientShader.MakeLinear([skia.Point(0, y0), skia.Point(0, y1)], [skia.Color(255, 232, 170), skia.Color(232, 182, 92), skia.Color(198, 146, 62)], [0, .55, 1])

def fundo():
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    t = (yy / H)[..., None]
    img = np.array([14, 26, 62], np.float32) * (1 - t) + np.array([8, 16, 40], np.float32) * t
    rng = np.random.default_rng(7)
    tex = cv2.GaussianBlur(rng.normal(0, 1, (H // 4, W // 4)).astype(np.float32), (0, 0), 1.2); tex = cv2.resize(tex, (W, H))
    img += (tex * 3.5 + rng.normal(0, 1.8, (H, W)).astype(np.float32))[..., None]   # textura de papel
    v = np.sqrt(((xx - W / 2) / W) ** 2 + ((yy - H * .45) / H) ** 2); img *= (1 - .35 * np.clip(v * 1.6 - .2, 0, 1))[..., None]
    rgba = np.zeros((H, W, 4), np.uint8); rgba[..., :3] = np.clip(img, 0, 255); rgba[..., 3] = 255
    return rgba

def brilho(rgba, cx, cy, rx, ry, forca, cor=(255, 196, 90)):
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    g = np.exp(-(((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2)) * forca
    rgba[..., :3] = np.clip(rgba[..., :3] + np.array(cor, np.float32) * g[..., None], 0, 255).astype(np.uint8)

def colinas(c, cy_luz):
    def morro(pts, cor, borda=60):
        p = skia.Path(); p.moveTo(*pts[0])
        for i in range(1, len(pts), 3): p.cubicTo(*pts[i], *pts[i + 1], *pts[i + 2])
        p.lineTo(pts[-1][0], H); p.lineTo(pts[0][0], H); p.close()
        ys = min(y for _, y in pts)
        sh = skia.GradientShader.MakeLinear([skia.Point(0, ys), skia.Point(0, ys + 420)], [skia.Color(cor[0] + 8, cor[1] + 12, cor[2] + 24), skia.Color(*cor)])
        c.drawPath(p, skia.Paint(AntiAlias=True, Shader=sh))
        c.drawPath(p, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=3, Color=skia.Color(110, 130, 190, borda)))
    morro([(0, 1060), (700, 1000), (1700, 1010), (W, 1040)], (14, 24, 60), 30)                      # fundo
    morro([(0, 870), (380, 850), (760, 960), (1180, 1240), (1180, 1240), (1180, 1240), (1180, 1240)], (15, 26, 64), 45)   # morro esquerdo
    morro([(1380, 1240), (1800, 960), (2180, 850), (W, 880)], (15, 26, 64), 45)                           # morro direito
    morro([(0, 1250), (800, 1120), (1760, 1120), (W, 1260)], (11, 20, 50), 40)                          # frente
    morro([(0, 1360), (900, 1290), (1700, 1300), (W, 1370)], (8, 15, 38), 25)

def estrela4(c, x, y, r, a=230):
    p = skia.Path(); p.moveTo(x, y - r); p.quadTo(x, y, x + r * .9, y); p.quadTo(x, y, x, y + r); p.quadTo(x, y, x - r * .9, y); p.quadTo(x, y, x, y - r); p.close()
    c.drawPath(p, skia.Paint(AntiAlias=True, Color=skia.Color(245, 205, 130, a)))

def lamparina(c, cx, cy, s):
    """Lamparina de óleo antiga (barro), dourada, com chama acesa. cy = base."""
    corpo = skia.Path()
    corpo.moveTo(cx - 230 * s, cy - 70 * s)
    corpo.cubicTo(cx - 240 * s, cy - 170 * s, cx + 120 * s, cy - 190 * s, cx + 160 * s, cy - 120 * s)   # topo
    corpo.lineTo(cx + 330 * s, cy - 150 * s)                                                          # bico
    corpo.cubicTo(cx + 380 * s, cy - 150 * s, cx + 380 * s, cy - 95 * s, cx + 330 * s, cy - 90 * s)
    corpo.cubicTo(cx + 200 * s, cy - 40 * s, cx + 120 * s, cy - 10 * s, cx + 40 * s, cy - 5 * s)
    corpo.cubicTo(cx - 100 * s, cy, cx - 220 * s, cy - 20 * s, cx - 230 * s, cy - 70 * s); corpo.close()
    c.drawPath(corpo, skia.Paint(AntiAlias=True, Shader=ouro_grad(cy - 190 * s, cy)))
    c.save(); c.clipPath(corpo, skia.ClipOp.kIntersect, True)
    c.drawPaint(skia.Paint(Shader=skia.GradientShader.MakeRadial(skia.Point(cx + 220 * s, cy - 170 * s), 420 * s,
        [skia.Color(255, 250, 220, 170), skia.Color(255, 230, 170, 0)])))
    c.drawPaint(skia.Paint(Shader=skia.GradientShader.MakeLinear([skia.Point(0, cy - 80 * s), skia.Point(0, cy)], [skia.Color(90, 50, 10, 0), skia.Color(90, 50, 10, 120)])))
    c.restore()
    # alça
    alca = skia.Path(); alca.moveTo(cx - 215 * s, cy - 120 * s); alca.cubicTo(cx - 340 * s, cy - 150 * s, cx - 340 * s, cy - 40 * s, cx - 220 * s, cy - 55 * s)
    c.drawPath(alca, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=26 * s, StrokeCap=skia.Paint.kRound_Cap, Shader=ouro_grad(cy - 150 * s, cy)))
    # boca de óleo e friso
    c.drawOval(skia.Rect(cx - 95 * s, cy - 172 * s, cx + 35 * s, cy - 138 * s), skia.Paint(AntiAlias=True, Color=skia.Color(150, 100, 40)))
    c.drawPath(corpo, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=4 * s, Color=skia.Color(255, 236, 190, 140)))
    fr = skia.Path(); fr.moveTo(cx - 200 * s, cy - 60 * s); fr.cubicTo(cx - 60 * s, cy - 30 * s, cx + 120 * s, cy - 40 * s, cx + 300 * s, cy - 95 * s)
    c.drawPath(fr, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=5 * s, Color=skia.Color(160, 110, 45, 160)))
    # chama
    fx, fy = cx + 350 * s, cy - 150 * s
    for r, a in ((190, 70), (110, 120), (60, 200)):
        c.drawCircle(fx, fy - 70 * s, r * s, skia.Paint(AntiAlias=True, Color=skia.Color(255, 210, 120, a), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, r * s * .55)))
    ch = skia.Path(); ch.moveTo(fx, fy - 175 * s); ch.cubicTo(fx + 55 * s, fy - 95 * s, fx + 45 * s, fy - 15 * s, fx, fy)
    ch.cubicTo(fx - 45 * s, fy - 15 * s, fx - 55 * s, fy - 95 * s, fx, fy - 175 * s); ch.close()
    c.drawPath(ch, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear([skia.Point(0, fy - 175 * s), skia.Point(0, fy)], [skia.Color(255, 220, 140), skia.Color(255, 250, 225)])))
    ci = skia.Path(); ci.moveTo(fx, fy - 95 * s); ci.cubicTo(fx + 22 * s, fy - 55 * s, fx + 18 * s, fy - 10 * s, fx, fy - 4 * s); ci.cubicTo(fx - 18 * s, fy - 10 * s, fx - 22 * s, fy - 55 * s, fx, fy - 95 * s)
    c.drawPath(ci, skia.Paint(AntiAlias=True, Color=skia.Color(255, 255, 250)))

def raios(c, cx, cy, n, r1, r2, a=110, larg=4):
    for k in range(n):
        ang = math.pi + (k + .5) / n * math.pi
        rr = r2 * (1 if k % 2 == 0 else .72)
        c.drawLine(cx + r1 * math.cos(ang), cy + r1 * math.sin(ang), cx + rr * math.cos(ang), cy + rr * math.sin(ang),
                   skia.Paint(AntiAlias=True, Color=skia.Color(255, 214, 140, a), StrokeWidth=larg, StrokeCap=skia.Paint.kRound_Cap))

def titulo(c, rot, num, promessa):
    f = M.F('Cinzel-Bold', 300); fn = M.F('Cinzel-Bold', 380)
    w1 = f.measureText(rot); w2 = fn.measureText(num); gap = 40; x0 = W / 2 - (w1 + gap + w2) / 2; by = 490
    sombra = skia.Paint(AntiAlias=True, Color=skia.Color(0, 0, 0, 160), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 14))
    c.drawString(rot, x0 + 6, by + 10, f, sombra)
    c.drawString(rot, x0, by, f, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear([skia.Point(0, by - 220), skia.Point(0, by)], [skia.Color(255, 251, 240), skia.Color(240, 230, 208)])))
    xn = x0 + w1 + gap
    c.drawString(num, xn, by + 20, fn, skia.Paint(AntiAlias=True, Color=skia.Color(255, 200, 110, 120), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 30)))
    c.drawString(num, xn + 6, by + 30, fn, sombra)
    c.drawString(num, xn, by + 20, fn, skia.Paint(AntiAlias=True, Shader=ouro_grad(by - 280, by + 20)))
    # linha + estrela
    y = 560; xa, xb = x0 - 10, xn + w2 + 10
    ln = skia.Paint(AntiAlias=True, Color=skia.Color(232, 192, 118, 230), StrokeWidth=5)
    c.drawLine(xa, y, W / 2 - 60, y, ln); c.drawLine(W / 2 + 60, y, xb, y, ln); estrela4(c, W / 2, y, 34, 255)
    fp = M.F('Cinzel-Bold', 120); wp = fp.measureText(promessa); yp = 695
    c.drawString(promessa, W / 2 - wp / 2 + 4, yp + 8, fp, sombra)
    c.drawString(promessa, W / 2 - wp / 2, yp, fp, skia.Paint(AntiAlias=True, Shader=ouro_grad(yp - 95, yp + 10)))

def capa(rot, num, promessa, objeto, saida):
    rgba = fundo()
    ox, oy = W / 2, 1180
    brilho(rgba, ox + 380, oy - 420, 380, 280, .5, (255, 170, 60)); brilho(rgba, ox, oy - 160, 1250, 360, .14, (255, 160, 60))
    s = skia.Surface(rgba)
    with s as c:
        colinas(c, oy)
        c.save(); c.clipRect(skia.Rect(0, 745, W, H))
        fx, fy = ox - 60 + 350 * 1.25, oy - 25 - 150 * 1.25 - 90
        for k in range(13):
            ang = math.pi * 1.0 + k / 12 * math.pi; rr = 330 if k % 2 == 0 else 250
            c.drawLine(fx + 150 * math.cos(ang), fy + 150 * math.sin(ang), fx + rr * math.cos(ang), fy + rr * math.sin(ang),
                       skia.Paint(AntiAlias=True, Color=skia.Color(255, 214, 140, 120), StrokeWidth=5, StrokeCap=skia.Paint.kRound_Cap))
        c.restore()
        luz = skia.Paint(AntiAlias=True, Color=skia.Color(255, 180, 80, 38), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 90))
        c.drawOval(skia.Rect(ox - 500, oy - 160, ox + 700, oy - 20), luz)
        objeto(c, ox - 60, oy - 25, 1.25)
        for x, y, r in [(215, 515, 30), (2240, 620, 26), (520, 830, 18), (1960, 880, 16), (2450, 425, 0), (160, 230, 0), (115, 645, 0), (355, 690, 0), (1790, 825, 0), (2070, 815, 0)]:
            estrela4(c, x, y, r) if r else c.drawCircle(x, y, 6, skia.Paint(AntiAlias=True, Color=skia.Color(245, 205, 130, 210)))
        titulo(c, rot, num, promessa)
        M.emblema(c, W - 205, 130, 230, T)
    rng = np.random.default_rng(3); tex = cv2.resize(cv2.GaussianBlur(rng.normal(0, 1, (H // 3, W // 3)).astype(np.float32), (0, 0), 1), (W, H))
    rgba[..., :3] = np.clip(rgba[..., :3].astype(np.float32) * (1 + tex[..., None] * .035), 0, 255).astype(np.uint8)
    out = cv2.cvtColor(rgba, cv2.COLOR_RGBA2BGR)
    cv2.imwrite(saida, out, [cv2.IMWRITE_JPEG_QUALITY, 92])

if __name__ == '__main__':
    capa('SALMO', '27', 'SEM MEDO ESTA NOITE', lamparina, sys.argv[1] if len(sys.argv) > 1 else '/home/claude/dadiva-dos-ceus/marca/capas-longos/salmo-27.jpg')
