"""Identidade v4: três variações premium (linha fina / claro / ícone sólido)."""
import os, math, sys, numpy as np, cv2, skia
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TF = lambda n: skia.Typeface.MakeFromFile(f'{R}/fontes/{n}.ttf')
def F(n, t, wght=None):
    tf = TF(n)
    if wght:
        tag = skia.FontArguments.VariationPosition.Coordinate((ord('w') << 24) | (ord('g') << 16) | (ord('h') << 8) | ord('t'), wght)
        tf = tf.makeClone(skia.FontArguments().setVariationDesignPosition(skia.FontArguments.VariationPosition(skia.FontArguments.VariationPosition.Coordinates([tag]))))
    return skia.Font(tf, t)
C = lambda r, g, b, a=255: skia.Color(r, g, b, a)
TEMAS = {
  'linha':  dict(bg=((14, 24, 48), (8, 14, 30)), ouro=C(222, 186, 118), claro=C(246, 236, 214), sub=C(214, 200, 172), estilo='linha'),
  'claro':  dict(bg=((248, 243, 232), (238, 229, 210)), ouro=C(176, 134, 62), claro=C(22, 34, 66), sub=C(96, 80, 56), estilo='linha'),
  'solido': dict(bg=((16, 30, 62), (9, 17, 38)), ouro=C(230, 192, 118), claro=C(250, 242, 224), sub=C(222, 208, 180), estilo='solido'),
}
def fundo(w, h, T):
    t = np.linspace(0, 1, h, dtype=np.float32)[:, None, None]
    a, b = np.array(T['bg'][0], np.float32), np.array(T['bg'][1], np.float32)
    img = np.broadcast_to(a * (1 - t) + b * t, (h, w, 3)).copy()
    img += np.random.default_rng(1).normal(0, 1.6, img.shape).astype(np.float32)  # grão sutil, evita faixas
    rgba = np.zeros((h, w, 4), np.uint8); rgba[..., :3] = np.clip(img, 0, 255); rgba[..., 3] = 255
    return rgba

def emblema(c, cx, cy, S, T):
    ouro = T['ouro']; lw = S * .022
    stroke = skia.Paint(AntiAlias=True, Color=ouro, Style=skia.Paint.kStroke_Style, StrokeWidth=lw, StrokeCap=skia.Paint.kRound_Cap, StrokeJoin=skia.Paint.kRound_Join)
    fill = skia.Paint(AntiAlias=True, Color=ouro)
    sr = S * .22; sy = cy - S * .04
    # sol
    if T['estilo'] == 'solido':
        c.save(); c.clipRect(skia.Rect(cx - S, cy - S, cx + S, sy - S * .035)); c.drawCircle(cx, sy, sr, fill); c.restore()
    else:
        arc = skia.Path(); arc.addArc(skia.Rect(cx - sr, sy - sr, cx + sr, sy + sr), 180, 180); c.drawPath(arc, stroke)
    for k in range(9):
        a = math.pi + (k + 1) / 10 * math.pi; r1 = sr * 1.28; r2 = sr * (1.78 if k % 2 == 0 else 1.55)
        c.drawLine(cx + r1 * math.cos(a), sy + r1 * math.sin(a), cx + r2 * math.cos(a), sy + r2 * math.sin(a),
                   skia.Paint(AntiAlias=True, Color=ouro, StrokeWidth=lw * .8, StrokeCap=skia.Paint.kRound_Cap))
    # livro
    w2, top, bot = S * .5, sy, sy + S * .30; gap = S * (.012 if T['estilo'] == 'solido' else .02)
    for sg in (-1, 1):
        x0 = cx + sg * gap
        dip = 0 if T['estilo'] == 'solido' else S * .03
        p = skia.Path(); p.moveTo(x0, top + dip)
        p.cubicTo(x0 + sg * w2 * .35, top - S * .04 + dip * .3, x0 + sg * w2 * .75, top - S * .03, cx + sg * w2, top + S * .02)
        p.lineTo(cx + sg * w2, bot); p.cubicTo(x0 + sg * w2 * .75, bot - S * .05, x0 + sg * w2 * .35, bot - S * .06, x0, bot); p.close()
        if T['estilo'] == 'solido':
            c.drawPath(p, fill)
            if sg == 1:  # vinco central na cor do fundo (separa as páginas sem mostrar o sol)
                mid = [int(T['bg'][0][i] * .5 + T['bg'][1][i] * .5) for i in range(3)]
                c.drawLine(cx, top - S * .01, cx, bot + S * .01, skia.Paint(AntiAlias=True, Color=skia.Color(*mid), StrokeWidth=gap * 2.2))
        else:
            bgc = skia.Color(*[int(v) for v in T['bg'][0]]) if False else None
            c.drawPath(p, stroke)


def wordmark(c, x, cy, esc, T, centro=False):
    f1 = F('CormorantGaramond', 150 * esc, 500); f2 = F('Cinzel', 38 * esc)
    t2 = 'DOS  CÉUS'; esp2 = 14 * esc
    w1 = f1.measureText('Dádiva'); w2 = sum(f2.measureText(ch) for ch in t2) + esp2 * (len(t2) - 1)
    if centro: x = x - max(w1, w2) / 2
    c.drawString('Dádiva', x, cy, f1, skia.Paint(AntiAlias=True, Color=T['claro']))
    xx = x + (w1 - w2) / 2
    for ch in t2: c.drawString(ch, xx, cy + 82 * esc, f2, skia.Paint(AntiAlias=True, Color=T['ouro'])); xx += f2.measureText(ch) + esp2
    return max(w1, w2)

def avatar(T, saida, S=1000):
    rgba = fundo(S, S, T); s = skia.Surface(rgba)
    with s as c: emblema(c, S / 2, S * .52, S * .62, T)
    cv2.imwrite(saida, cv2.cvtColor(rgba, cv2.COLOR_RGBA2BGR))

def banner(T, saida, W, H, esc):
    rgba = fundo(W, H, T); s = skia.Surface(rgba)
    with s as c:
        ew = 300 * esc; f1 = F('CormorantGaramond', 150 * esc, 500); w1 = f1.measureText('Dádiva')
        total = ew + 60 * esc + w1; x0 = W / 2 - total / 2
        emblema(c, x0 + ew / 2, H / 2 - 20 * esc, ew, T)
        c.drawLine(x0 + ew + 30 * esc, H / 2 - 95 * esc, x0 + ew + 30 * esc, H / 2 + 75 * esc, skia.Paint(AntiAlias=True, Color=skia.ColorSetA(T['ouro'], 120), StrokeWidth=2 * esc))
        wordmark(c, x0 + ew + 60 * esc, H / 2 + 8 * esc, esc, T)
        ft = F('Cinzel', 26 * esc); tl = 'LEITURAS PARA DORMIR   ·   LOUVORES   ·   HISTÓRIAS DA BÍBLIA'
        tw = ft.measureText(tl); c.drawString(tl, W / 2 - tw / 2, H / 2 + 190 * esc, ft, skia.Paint(AntiAlias=True, Color=T['sub']))
    cv2.imwrite(saida, cv2.cvtColor(rgba, cv2.COLOR_RGBA2BGR))

if __name__ == '__main__':
    o = f'{R}/marca/v4'; os.makedirs(o, exist_ok=True)
    for nome, T in TEMAS.items():
        avatar(T, f'{o}/avatar-{nome}.png'); banner(T, f'{o}/banner-youtube-{nome}.png', 2560, 1440, 1.75); banner(T, f'{o}/capa-facebook-{nome}.png', 1640, 624, 1.0)
