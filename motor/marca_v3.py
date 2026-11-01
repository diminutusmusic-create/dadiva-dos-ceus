"""Identidade v3: vetorial e limpa. Emblema = Bíblia aberta com a luz nascendo das páginas (dádiva que vem do céu)."""
import os, math, numpy as np, cv2, skia
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
F = lambda n, t: skia.Font(skia.Typeface.MakeFromFile(f'{R}/fontes/{n}.ttf'), t)
OURO = skia.Color(236, 196, 120); OURO2 = skia.Color(250, 226, 170); CREME = skia.Color(255, 248, 234)
NOITE1, NOITE2 = (11, 21, 46), (24, 44, 86)

def fundo(w, h, brilho=(0.5, 0.42), estrelas=True, seed=4):
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    t = np.clip(yy / h, 0, 1)[..., None]
    img = np.array(NOITE2, np.float32) * (1 - t) + np.array(NOITE1, np.float32) * t
    d = np.sqrt(((xx - w * brilho[0]) / (w * .55)) ** 2 + ((yy - h * brilho[1]) / (h * .75)) ** 2)
    g = np.clip(1 - d, 0, 1) ** 2.2
    img = img + np.array([88, 62, 18], np.float32) * g[..., None] * .85   # halo dourado quente
    rgba = np.zeros((h, w, 4), np.uint8); rgba[..., :3] = np.clip(img, 0, 255); rgba[..., 3] = 255
    s = skia.Surface(rgba)
    if estrelas:
        r = np.random.default_rng(seed)
        with s as c:
            for _ in range(int(w * h / 9000)):
                x, y = r.uniform(0, w), r.uniform(0, h * .8); a = int(r.uniform(40, 170) * (1 - y / h))
                c.drawCircle(x, y, r.uniform(.8, 2.2) * w / 2560 * 1.6, skia.Paint(AntiAlias=True, Color=skia.Color(255, 245, 220, a)))
    return rgba

def emblema(c, cx, cy, S):
    """S = largura do livro. Livro aberto com sol nascendo e raios."""
    ouro = skia.Paint(AntiAlias=True, Color=OURO, Style=skia.Paint.kStroke_Style, StrokeWidth=S * .028, StrokeCap=skia.Paint.kRound_Cap, StrokeJoin=skia.Paint.kRound_Join)
    fino = skia.Paint(AntiAlias=True, Color=OURO2, StrokeWidth=S * .014, StrokeCap=skia.Paint.kRound_Cap)
    # sol (semicírculo) atrás do livro
    sr = S * .26; sy = cy - S * .02
    glow = skia.Paint(AntiAlias=True, Color=skia.Color(255, 214, 140, 110), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, S * .09))
    c.drawCircle(cx, sy, sr * 1.05, glow)
    c.save(); c.clipRect(skia.Rect(cx - S, cy - S, cx + S, sy))
    sh = skia.GradientShader.MakeLinear([skia.Point(cx, sy - sr), skia.Point(cx, sy)], [skia.Color(255, 240, 200), skia.Color(240, 190, 105)])
    c.drawCircle(cx, sy, sr, skia.Paint(AntiAlias=True, Shader=sh))
    c.restore()
    # raios
    for k in range(11):
        a = math.pi + (k + 1) / 12 * math.pi
        r1, r2 = sr * 1.25, sr * (1.95 if k % 2 == 0 else 1.65)
        da = .022 if k % 2 == 0 else .016; tri = skia.Path()
        tri.moveTo(cx + r1 * math.cos(a - da), sy + r1 * math.sin(a - da)); tri.lineTo(cx + r2 * math.cos(a), sy + r2 * math.sin(a))
        tri.lineTo(cx + r1 * math.cos(a + da), sy + r1 * math.sin(a + da)); tri.close()
        c.drawPath(tri, skia.Paint(AntiAlias=True, Color=OURO2))
    # livro aberto: duas páginas curvas
    w2, top, bot = S / 2, cy - S * .02, cy + S * .30
    for sg in (-1, 1):
        p = skia.Path(); p.moveTo(cx, top + S * .04)
        p.cubicTo(cx + sg * w2 * .35, top - S * .05, cx + sg * w2 * .75, top - S * .04, cx + sg * w2, top + S * .02)
        p.lineTo(cx + sg * w2, bot)
        p.cubicTo(cx + sg * w2 * .75, bot - S * .06, cx + sg * w2 * .35, bot - S * .07, cx, bot)
        p.close()
        folhas = skia.Path(p); folhas.offset(0, S * .035)
        c.drawPath(folhas, skia.Paint(AntiAlias=True, Color=skia.ColorSetA(OURO, 150), Style=skia.Paint.kStroke_Style, StrokeWidth=S * .016))
        shp = skia.GradientShader.MakeLinear([skia.Point(cx, top), skia.Point(cx, bot)], [skia.Color(34, 58, 108), skia.Color(16, 30, 64)])
        c.drawPath(p, skia.Paint(AntiAlias=True, Shader=shp))  # tampa o sol atrás
        c.drawPath(p, ouro)
        for i in (1, 2):  # linhas de texto
            yl = top + S * .04 + i * S * .062
            c.drawLine(cx + sg * w2 * .2, yl, cx + sg * w2 * .78, yl - S * .012, skia.Paint(AntiAlias=True, Color=skia.ColorSetA(OURO, 120), StrokeWidth=S * .01, StrokeCap=skia.Paint.kRound_Cap))
    c.drawLine(cx, top + S * .04, cx, bot, ouro)

def texto(c, t, x, y, f, cor, centro=True, esp=0):
    if esp:
        tot = sum(f.measureText(ch) for ch in t) + esp * (len(t) - 1); x = x - tot / 2 if centro else x
        for ch in t: c.drawString(ch, x, y, f, skia.Paint(AntiAlias=True, Color=cor)); x += f.measureText(ch) + esp
        return
    if centro: x -= f.measureText(t) / 2
    c.drawString(t, x, y, f, skia.Paint(AntiAlias=True, Color=cor))

def salvar(rgba, p): cv2.imwrite(p, cv2.cvtColor(rgba, cv2.COLOR_RGBA2BGR))

def avatar(saida, S=1000):
    rgba = fundo(S, S, (0.5, 0.45), estrelas=True, seed=2); s = skia.Surface(rgba)
    with s as c:
        emblema(c, S / 2, S * .56, S * .64)
        c.drawCircle(S / 2, S / 2, S * .47, skia.Paint(AntiAlias=True, Color=skia.ColorSetA(OURO, 150), Style=skia.Paint.kStroke_Style, StrokeWidth=S * .008))
    salvar(rgba, saida)

def marca_horizontal(c, x, cy, esc):
    emblema(c, x + 130 * esc, cy + 4 * esc, 290 * esc)
    f = F('Cinzel-Bold', 100 * esc); esp = 7 * esc; t = 'DÁDIVA DOS CÉUS'
    larg = sum(f.measureText(ch) for ch in t) + esp * (len(t) - 1); x0 = x + 320 * esc
    texto(c, t, x0, cy + 18 * esc, f, CREME, centro=False, esp=esp)
    ln = skia.Paint(AntiAlias=True, Color=skia.ColorSetA(OURO, 190), StrokeWidth=2 * esc); yl = cy + 52 * esc; mid = x0 + larg / 2
    c.drawLine(x0, yl, mid - 18 * esc, yl, ln); c.drawLine(mid + 18 * esc, yl, x0 + larg, yl, ln)
    d = skia.Path(); d.moveTo(mid, yl - 8 * esc); d.lineTo(mid + 8 * esc, yl); d.lineTo(mid, yl + 8 * esc); d.lineTo(mid - 8 * esc, yl); d.close()
    c.drawPath(d, skia.Paint(AntiAlias=True, Color=OURO))
    ft = F('Cinzel', 27 * esc); tl = 'LEITURAS PARA DORMIR  ·  LOUVORES  ·  HISTÓRIAS DA BÍBLIA'
    lt = sum(ft.measureText(ch) for ch in tl) + 3 * esc * (len(tl) - 1)
    texto(c, tl, mid, cy + 98 * esc, ft, OURO2, centro=True, esp=3 * esc)

def largura_marca(esc):
    f = F('Cinzel-Bold', 100 * esc); t = 'DÁDIVA DOS CÉUS'
    return 320 * esc + sum(f.measureText(ch) for ch in t) + 7 * esc * (len(t) - 1)

def banner_yt(saida):
    W, H = 2560, 1440; rgba = fundo(W, H, (0.5, 0.5)); s = skia.Surface(rgba)
    with s as c: marca_horizontal(c, W / 2 - largura_marca(1.2) / 2 - 10, H / 2, 1.2)
    salvar(rgba, saida)

def capa_fb(saida):
    W, H = 1640, 624; rgba = fundo(W, H, (0.5, 0.5)); s = skia.Surface(rgba)
    with s as c: marca_horizontal(c, W / 2 - largura_marca(.78) / 2 - 10, H / 2, .78)
    salvar(rgba, saida)

if __name__ == '__main__':
    o = f'{R}/marca/v3'; os.makedirs(o, exist_ok=True)
    avatar(f'{o}/avatar.png'); banner_yt(f'{o}/banner-youtube.png'); capa_fb(f'{o}/capa-facebook.png')
