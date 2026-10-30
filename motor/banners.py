"""Banner do YouTube (2560x1440) e capa do Facebook (1640x624) — Dádiva dos Céus."""
import math, skia
from cartoon_rig import cutout, to_skia
from engine import font, hexc
samp = skia.SamplingOptions(skia.FilterMode.kLinear, skia.MipmapMode.kLinear)
def P(c, a=255): return skia.Paint(AntiAlias=True, Color=hexc(c, a))
def St(c, w):
    p = P(c); p.setStyle(skia.Paint.kStroke_Style); p.setStrokeWidth(w)
    p.setStrokeJoin(skia.Paint.kRound_Join); p.setStrokeCap(skia.Paint.kRound_Cap); return p
LINE = '#4a2412'
chars = {k: to_skia(cutout(f'arte/{k}.png')) for k in ('jesus_101', 'davi_101')}

def landscape(c, W, H, sun):
    sh = skia.GradientShader.MakeLinear([(0, 0), (0, H)], [hexc('#6fb8ea'), hexc('#bfe2f6'), hexc('#fff0bf')], [0, .5, .8])
    c.drawRect(skia.Rect(0, 0, W, H), skia.Paint(Shader=sh))
    sx, sy = sun
    c.save(); c.translate(sx, sy)
    for k in range(24):
        c.rotate(15); p = skia.Path(); p.moveTo(0, 0); p.lineTo(-70, -3000); p.lineTo(70, -3000); p.close(); c.drawPath(p, P('#ffffff', 45))
    c.restore()
    g = skia.GradientShader.MakeRadial((sx, sy), H * .6, [hexc('#ffffff', 240), hexc('#fff6d0', 0)], [0, 1])
    c.drawRect(skia.Rect(0, 0, W, H), skia.Paint(Shader=g))
    def hill(base, amp, freq, ph, col):
        p = skia.Path(); p.moveTo(-20, H + 20)
        for x in range(-20, W + 40, 16): p.lineTo(x, base + math.sin(x * freq + ph) * amp + math.sin(x * freq * 2.3 + ph * 2) * amp * .3)
        p.lineTo(W + 40, H + 20); p.close(); c.drawPath(p, P(col)); c.drawPath(p, St(LINE, 5))
    hill(H * .66, H * .05, 6.6 / W, 1, '#a9d18e')
    c.drawRect(skia.Rect(0, H * .73, W, H * .79), P('#5cc0e6')); c.drawLine(0, H * .73, W, H * .73, St(LINE, 5))
    for k in range(int(W / 90)):
        x = (k * 97) % W; y = H * .745 + (k * 31 % 40) * H / 1400
        c.drawLine(x, y, x + 40, y, St('#ffffff', 4))
    hill(H * .80, H * .03, 7.5 / W, 3, '#8cc66a')
    hill(H * .90, H * .025, 9 / W, 5, '#76b356')

def cloud(c, x, y, s):
    p = skia.Path()
    for dx, dy, r in [(-60, 0, 45), (-15, -25, 55), (35, -10, 48), (70, 5, 35), (0, 10, 45)]: p.addCircle(x + dx * s, y + dy * s, r * s)
    c.drawPath(p, St(LINE, 5)); c.drawPath(p, P('#ffffff'))

def figure(c, key, cx, bottom, height):
    im = chars[key]; s = height / im.height()
    c.save(); c.translate(cx - im.width() * s / 2, bottom - im.height() * s); c.scale(s, s); c.drawImage(im, 0, 0, samp); c.restore()

def title(c, cx, y, size, sub_size):
    f = font('Cinzel-Bold', size); t = 'DÁDIVA DOS CÉUS'; w = f.measureText(t)
    c.drawString(t, cx - w / 2, y + 8, f, P('#000000', 60))
    c.drawString(t, cx - w / 2, y, f, St(LINE, size * .16)); c.drawString(t, cx - w / 2, y, f, P('#fff3cf'))
    f2 = font('Cormorant-Bold', sub_size); t2 = 'Histórias da Bíblia animadas'; w2 = f2.measureText(t2)
    rw = w2 + sub_size * 1.4; rh = sub_size * 1.45; ry = y + sub_size * .55
    r = skia.RRect.MakeRectXY(skia.Rect(cx - rw / 2, ry, cx + rw / 2, ry + rh), rh / 2, rh / 2)
    c.drawRRect(r, P('#c8352c')); c.drawRRect(r, St(LINE, 6))
    c.drawString(t2, cx - w2 / 2, ry + rh * .72, f2, P('#ffffff'))
    return w

# ---- YouTube 2560x1440 (área segura: 1546x423 no centro)
W, H = 2560, 1440; s = skia.Surface(W, H); c = s.getCanvas()
landscape(c, W, H, (W / 2, H * .38))
for x, y, sc in [(300, 330, 1.6), (2250, 300, 1.8), (900, 250, 1.1), (1700, 230, 1.2), (150, 700, 1.2), (2420, 680, 1.3)]: cloud(c, x, y, sc)
figure(c, 'jesus_101', 660, 935, 420); figure(c, 'davi_101', 1900, 935, 360)
title(c, W / 2, 712, 96, 46)
s.makeImageSnapshot().save('saida/perfil/banner-youtube.png', skia.kPNG)
pv = skia.Surface(W, H); pc = pv.getCanvas(); pc.drawImage(s.makeImageSnapshot(), 0, 0)
pc.drawRect(skia.Rect(507, 508, 2053, 931), St('#ff00ff', 6))
pv.makeImageSnapshot().save('/tmp/yt_safe.png', skia.kPNG)

# ---- Facebook 1640x624
W, H = 1640, 624; s = skia.Surface(W, H); c = s.getCanvas()
landscape(c, W, H, (W * .42, H * .42))
for x, y, sc in [(160, 120, 1.0), (1500, 110, 1.1), (600, 90, .7), (1150, 80, .75)]: cloud(c, x, y, sc)
figure(c, 'jesus_101', 1270, 615, 560); figure(c, 'davi_101', 1490, 615, 420)
title(c, 620, 300, 92, 40)
s.makeImageSnapshot().save('saida/perfil/capa-facebook.png', skia.kPNG)
