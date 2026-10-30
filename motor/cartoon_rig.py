"""Animação de personagem a partir de uma ilustração (arte gerada por IA, recortada).
Camadas: corpo + cabeça (separada no pescoço) com respiração, balanço, piscada e boca falando."""
import math
import numpy as np
import skia
from PIL import Image, ImageFilter
from scipy import ndimage

def cutout(path, thr=235, erode=1):
    """remove o fundo branco ligado às bordas -> RGBA"""
    im = np.array(Image.open(path).convert('RGB'))
    white = im.min(2) > thr
    lab, _ = ndimage.label(white)
    border = set(np.unique(np.r_[lab[0], lab[-1], lab[:, 0], lab[:, -1]])) - {0}
    fg = ~np.isin(lab, list(border))
    if erode: fg = ndimage.binary_erosion(fg, iterations=erode)
    a = Image.fromarray((fg * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.9))
    return np.dstack([im, np.array(a)])

def to_skia(rgba):
    return skia.Image.fromarray(np.ascontiguousarray(rgba), colorType=skia.kRGBA_8888_ColorType)

def P(c, a=255):
    h = c.lstrip('#'); return skia.Paint(AntiAlias=True, Color=skia.Color(int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), a))
def S(c, w):
    p = P(c); p.setStyle(skia.Paint.kStroke_Style); p.setStrokeWidth(w); p.setStrokeCap(skia.Paint.kRound_Cap); return p

class Puppet:
    """rig de um personagem. 'spec' traz pontos na imagem original (px)."""
    def __init__(self, path, spec):
        rgba = cutout(path); self.spec = spec
        h, w = rgba.shape[:2]; self.w, self.h = w, h
        ny = spec.get('neck_y', 0); f = spec.get('feather', 18)
        m = np.clip((ny - np.arange(h)) / f + .5, 0, 1)[:, None]  # máscara da cabeça (some no pescoço)
        head = rgba.copy(); head[..., 3] = (head[..., 3] * m).astype(np.uint8)
        self.body = to_skia(rgba); self.head = to_skia(head) if ny else None
        ys, xs = np.where(rgba[..., 3] > 0); self.feet = (float(xs.mean()), float(ys.max()))

    def draw(self, c, x, y, scale, t, talk=0.0, blink=False, sway=1.0, look=0.0, flip=False):
        """x,y = posição dos pés na tela"""
        sp = self.spec; fx, fy = self.feet
        c.save(); c.translate(x, y); c.scale(-scale if flip else scale, scale)
        c.rotate(math.sin(t * .9) * .8 * sway)                      # balanço leve
        br = 1 + math.sin(t * 2.1) * .006                            # respiração
        c.scale(1 + (br - 1) * .5, br)
        c.translate(-fx, -fy)
        samp = skia.SamplingOptions(skia.FilterMode.kLinear, skia.MipmapMode.kLinear)
        c.drawImage(self.body, 0, 0, samp)
        if self.head is None:
            c.restore(); return
        # cabeça: inclina e balança em volta do pescoço
        px, py = sp['neck_pivot']
        ang = math.sin(t * 1.3) * 1.6 * sway + talk * math.sin(t * 9) * 1.2 + look
        nod = talk * abs(math.sin(t * 7)) * 2.5
        c.save(); c.translate(px, py + nod); c.rotate(ang); c.translate(-px, -py)
        c.drawImage(self.head, 0, 0, samp)
        self._face(c, talk, blink)
        c.restore()
        c.restore()

    def _face(self, c, talk, blink):
        sp = self.spec
        if blink:
            for ex, ey in sp['eyes']:
                rx, ry = sp['eye_r']
                c.drawOval(skia.Rect(ex - rx, ey - ry, ex + rx, ey + ry), P(sp['skin']))
                pth = skia.Path(); pth.moveTo(ex - rx * .9, ey + 2); pth.quadTo(ex, ey + ry * .55, ex + rx * .9, ey + 2)
                c.drawPath(pth, S(sp['line'], 5))
        if talk > .08:
            mx, my = sp['mouth']; mw = sp['mouth_w']
            pw, ph = sp['mouth_patch']
            c.drawOval(skia.Rect(mx - pw, my - ph, mx + pw, my + ph), P(sp['beard']))
            oh = 5 + talk * 20; ow = mw * (.75 + .25 * (1 - talk))
            r = skia.Rect(mx - ow / 2, my - oh * .35, mx + ow / 2, my + oh * .65)
            c.drawOval(r, P('#5a1a12'))
            c.save(); c.clipPath(skia.Path().addOval(r), doAntiAlias=True)
            c.drawRect(skia.Rect(r.left(), r.top(), r.right(), r.top() + 6), P('#ffffff'))
            c.drawOval(skia.Rect(mx - ow * .3, r.bottom() - oh * .45, mx + ow * .3, r.bottom() + 4), P('#d9605a'))
            c.restore()
            c.drawOval(r, S(sp['line'], 3.5))

JESUS = dict(neck_y=338, neck_pivot=(330, 345), feather=16,
             eyes=[(282, 212), (382, 212)], eye_r=(17, 22),
             mouth=(328, 272), mouth_w=40, mouth_patch=(30, 17),
             skin='#febf94', beard='#80411e', line='#531d0b')

RIGS = {'jesus_101': JESUS}
