"""Motor de animação 2D procedural — estilo silhueta (teatro de sombras) sobre céu pintado.
Tudo gerado por código: sem GPU, sem créditos, sem assets externos.
"""
import math, random
import numpy as np
import skia

W, H = 1080, 1920
FPS = 30
BASE = __import__('os').path.dirname(__import__('os').path.abspath(__file__))

# ---------------------------------------------------------------- utilidades
def lerp(a, b, t): return a + (b - a) * t
def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def ease(t):  # ease in-out
    t = clamp(t); return t * t * (3 - 2 * t)
def ease_out(t): t = clamp(t); return 1 - (1 - t) ** 3
def ease_in(t): t = clamp(t); return t ** 3

def hexc(h, a=255):
    h = h.lstrip('#'); r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return skia.Color(r, g, b, a)

def mix(c1, c2, t):
    a = [int(c1[i:i+2], 16) for i in (1, 3, 5)]; b = [int(c2[i:i+2], 16) for i in (1, 3, 5)]
    return '#%02x%02x%02x' % tuple(int(lerp(x, y, t)) for x, y in zip(a, b))

def paint(color, alpha=255, stroke=None, cap=True, blur=0):
    p = skia.Paint(AntiAlias=True, Color=hexc(color, alpha) if isinstance(color, str) else color)
    if stroke:
        p.setStyle(skia.Paint.kStroke_Style); p.setStrokeWidth(stroke)
        if cap: p.setStrokeCap(skia.Paint.kRound_Cap); p.setStrokeJoin(skia.Paint.kRound_Join)
    if blur: p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, blur))
    return p

def noise1(x, seed=0):
    """ruído suave 1D (soma de senos) — determinístico"""
    r = random.Random(seed); v = 0; amp = 1
    for o in range(4):
        f = r.uniform(0.6, 1.4) * (2 ** o); ph = r.uniform(0, 6.28)
        v += math.sin(x * f + ph) * amp; amp *= 0.5
    return v / 1.875

# ---------------------------------------------------------------- tipografia
_tf = {}
def font(name, size):
    if name not in _tf:
        _tf[name] = skia.Typeface.MakeFromFile(f'{BASE}/../fontes/{name}.ttf')
    f = skia.Font(_tf[name], size); f.setEdging(skia.Font.Edging.kAntiAlias); f.setSubpixel(True); return f

def text_center(c, txt, y, f, color='#fff4e0', alpha=255, shadow=True, spacing=0, x=W/2, outline=None):
    if spacing:
        widths = [f.measureText(ch) + spacing for ch in txt]; total = sum(widths) - spacing
        cx = x - total / 2
        for ch, w in zip(txt, widths):
            if shadow: c.drawString(ch, cx, y + 4, f, paint('#000000', int(alpha * .7), blur=10))
            c.drawString(ch, cx, y, f, paint(color, alpha)); cx += w
        return
    w = f.measureText(txt)
    if shadow:
        c.drawString(txt, x - w / 2, y + 4, f, paint('#000000', int(alpha * .75), blur=12))
    if outline:
        c.drawString(txt, x - w / 2, y, f, paint(outline, alpha, stroke=12))
    c.drawString(txt, x - w / 2, y, f, paint(color, alpha))

# ---------------------------------------------------------------- cenário
class Palette:
    def __init__(self, sky_top, sky_mid, sky_low, sun, haze, silhouette='#140c08', rim='#ffb766'):
        self.sky_top, self.sky_mid, self.sky_low = sky_top, sky_mid, sky_low
        self.sun, self.haze, self.sil, self.rim = sun, haze, silhouette, rim

DUSK = Palette('#2a1a3a', '#b8573a', '#f2b36a', '#fff0c2', '#e89a5c')
DAY = Palette('#3d5f86', '#c98a5a', '#f5cf8e', '#fff6d8', '#e7b27a')
SUNSET = Palette('#1d1630', '#a3402f', '#ffb056', '#fff1b8', '#f08a4b')
OMEN = Palette('#1a1420', '#5e3328', '#c7743f', '#ffd49a', '#9a5a3a')

def sky(c, pal, sun_xy=(W*0.5, H*0.42), sun_r=110, t=0):
    sh = skia.GradientShader.MakeLinear([(0, 0), (0, H * 0.75)],
        [hexc(pal.sky_top), hexc(pal.sky_mid), hexc(pal.sky_low)], [0, 0.55, 1])
    c.drawRect(skia.Rect(0, 0, W, H), skia.Paint(Shader=sh))
    sx, sy = sun_xy
    glow = skia.GradientShader.MakeRadial((sx, sy), sun_r * 7,
        [hexc(pal.sun, 150), hexc(pal.haze, 60), hexc(pal.haze, 0)], [0, 0.35, 1])
    c.drawRect(skia.Rect(0, 0, W, H), skia.Paint(Shader=glow))
    c.drawCircle(sx, sy, sun_r, paint(pal.sun, 255, blur=6))
    # nuvens finas (faixas)
    for i in range(5):
        y = H * 0.18 + i * 95 + noise1(i, 3) * 30
        x = (noise1(i * 7, 5) * 300 + t * 6 * (1 + i * .3)) % (W + 900) - 450
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(x, y, x + 520 + i * 60, y + 16 + i * 3), 12, 12),
                    paint(pal.haze, 70 - i * 8, blur=9))

def ridge(c, y_base, amp, color, seed, alpha=255, freq=0.004, x_off=0, flat_center=None):
    p = skia.Path(); p.moveTo(-50, H + 50); p.lineTo(-50, y_base)
    for x in range(-50, W + 60, 12):
        n = noise1((x + x_off) * freq, seed)
        y = y_base - n * amp
        if flat_center:  # vale: rebaixa o centro
            cx, wdt, depth = flat_center
            y += depth * math.exp(-((x - cx) / wdt) ** 2)
        p.lineTo(x, y)
    p.lineTo(W + 60, H + 50); p.close()
    c.drawPath(p, paint(color, alpha))
    return lambda x: y_base - noise1((x + x_off) * freq, seed) * amp + (
        flat_center[2] * math.exp(-((x - flat_center[0]) / flat_center[1]) ** 2) if flat_center else 0)

def haze_band(c, y, h, color, alpha=90):
    sh = skia.GradientShader.MakeLinear([(0, y - h), (0, y + h)],
        [hexc(color, 0), hexc(color, alpha), hexc(color, 0)], [0, .5, 1])
    c.drawRect(skia.Rect(0, y - h, W, y + h), skia.Paint(Shader=sh))

def tent(c, x, y, s, color):
    p = skia.Path(); p.moveTo(x - 60 * s, y); p.lineTo(x, y - 70 * s); p.lineTo(x + 60 * s, y); p.close()
    c.drawPath(p, paint(color))
    c.drawLine(x, y - 70 * s, x, y - 95 * s, paint(color, stroke=3 * s))

def banner(c, x, y, s, color, t, seed=0):
    c.drawLine(x, y, x, y - 160 * s, paint(color, stroke=4 * s))
    p = skia.Path(); top = y - 160 * s; p.moveTo(x, top)
    for i in range(9):
        u = i / 8; p.lineTo(x + u * 70 * s, top + math.sin(t * 5 + u * 4 + seed) * 7 * s * u)
    for i in range(8, -1, -1):
        u = i / 8; p.lineTo(x + u * 70 * s, top + 34 * s + math.sin(t * 5 + u * 4 + seed + .5) * 7 * s * u)
    p.close(); c.drawPath(p, paint(color))

class Dust:
    """partículas de poeira/luz flutuando"""
    def __init__(self, n=90, seed=1, color='#ffd9a0'):
        r = random.Random(seed)
        self.p = [(r.uniform(0, W), r.uniform(0, H), r.uniform(1.2, 4.5), r.uniform(.2, 1), r.uniform(0, 6.28)) for _ in range(n)]
        self.color = color
    def draw(self, c, t, alpha=1.0, wind=18):
        for x, y, sz, sp, ph in self.p:
            xx = (x + t * wind * sp * 3 + math.sin(t * .7 + ph) * 20) % W
            yy = (y - t * 12 * sp + math.cos(t * .5 + ph) * 15) % H
            a = int((90 + 90 * math.sin(t * 1.3 + ph)) * alpha)
            c.drawCircle(xx, yy, sz, paint(self.color, max(0, min(255, a)), blur=sz * .8))

def dust_cloud(c, x, y, t, strength, color='#c9905c', seed=4):
    """nuvem de poeira que sobe (t de 0 a 1)"""
    r = random.Random(seed)
    for i in range(40):
        ang = r.uniform(math.pi, 2 * math.pi); sp = r.uniform(80, 420)
        px = x + math.cos(ang) * sp * ease_out(t) * 1.4; py = y + math.sin(ang) * sp * .5 * ease_out(t)
        rad = r.uniform(40, 120) * (0.4 + t)
        a = int(strength * 120 * (1 - t) ** 1.2)
        c.drawCircle(px, py, rad, paint(color, max(0, a), blur=rad * .5))

# ---------------------------------------------------------------- personagens
NEUTRAL = dict(lean=0, head=0, ua_f=8, la_f=14, ua_b=-6, la_b=-2, th_f=4, sh_f=0, th_b=-4, sh_b=-6, drop=0)

def pose(**kw):
    d = dict(NEUTRAL); d.update(kw); return d

def blend(p1, p2, t):
    return {k: lerp(p1[k], p2[k], t) for k in p1}

def walk(phase, amp=1.0):
    s = math.sin(phase); c2 = math.cos(phase)
    return pose(lean=4, th_f=24 * s * amp, sh_f=24 * s * amp - 12 * amp * max(0, -c2),
                th_b=-24 * s * amp, sh_b=-24 * s * amp - 12 * amp * max(0, c2),
                ua_f=-18 * s * amp, la_f=-10 * s * amp + 10, ua_b=18 * s * amp, la_b=18 * s * amp + 6,
                drop=-abs(c2) * 3 * amp)

class Figure:
    """boneco articulado. dims em unidades (altura ~ 185 * scale)."""
    def __init__(self, kind='davi', scale=1.0):
        self.kind = kind; self.s = scale
        big = kind == 'golias'
        self.L = dict(shin=48, thigh=48, torso=62, neck=8, head=14 if not big else 15.5, ua=34, la=32)
        self.wd = dict(leg=15 if not big else 22, arm=11 if not big else 17, torso=28 if not big else 40)

    def joints(self, x, ground, p, facing):
        s, L, f = self.s, self.L, facing
        def d(a):  # direção a partir de "para baixo"
            r = math.radians(a); return (math.sin(r) * f, math.cos(r))
        def up(a):
            r = math.radians(a); return (math.sin(r) * f, -math.cos(r))
        hip = np.array([0.0, 0.0])
        kf = hip + np.array(d(p['th_f'])) * L['thigh'] * s; ff = kf + np.array(d(p['sh_f'])) * L['shin'] * s
        kb = hip + np.array(d(p['th_b'])) * L['thigh'] * s; fb = kb + np.array(d(p['sh_b'])) * L['shin'] * s
        low = max(ff[1], fb[1])
        off = np.array([x, ground - low - p['drop'] * s])
        J = dict(hip=hip, kf=kf, ff=ff, kb=kb, fb=fb)
        sh = hip + np.array(up(p['lean'])) * L['torso'] * s
        nk = sh + np.array(up(p['lean'] + p['head'] * .5)) * L['neck'] * s
        hd = nk + np.array(up(p['lean'] + p['head'])) * L['head'] * s
        ef = sh + np.array(d(p['ua_f'])) * L['ua'] * s; hf = ef + np.array(d(p['la_f'])) * L['la'] * s
        eb = sh + np.array(d(p['ua_b'])) * L['ua'] * s; hb = eb + np.array(d(p['la_b'])) * L['la'] * s
        J.update(sh=sh, nk=nk, hd=hd, ef=ef, hf=hf, eb=eb, hb=hb)
        return {k: v + off for k, v in J.items()}

    def draw(self, c, x, ground, p, facing=1, color='#140c08', rim=None, rim_dir=-1, extra=None):
        J = self.joints(x, ground, p, facing)
        if rim:  # contorno de luz (sol atrás)
            c.save(); c.translate(rim_dir * 3 * self.s, -1.5 * self.s)
            self._body(c, J, p, facing, paint(rim, 230, blur=3 * self.s), extra)
            c.restore()
        self._body(c, J, p, facing, paint(color), extra)
        return J

    def _limb(self, c, a, b, w, pt):
        q = skia.Paint(pt); q.setStyle(skia.Paint.kStroke_Style); q.setStrokeWidth(w)
        q.setStrokeCap(skia.Paint.kRound_Cap); c.drawLine(a[0], a[1], b[0], b[1], q)

    def _body(self, c, J, p, f, pt, extra):
        s, wd, big = self.s, self.wd, self.kind == 'golias'
        ex = extra or {}
        # braço de trás + escudo
        self._limb(c, J['sh'], J['eb'], wd['arm'] * s, pt); self._limb(c, J['eb'], J['hb'], wd['arm'] * .9 * s, pt)
        if big and ex.get('shield', True):
            c.drawCircle(J['hb'][0] - f * 6 * s, J['hb'][1] - 10 * s, 38 * s, pt)
        # pernas
        for k, ft in (('kb', 'fb'), ('kf', 'ff')):
            self._limb(c, J['hip'], J[k], wd['leg'] * s, pt); self._limb(c, J[k], J[ft], wd['leg'] * .85 * s, pt)
            foot = skia.Path(); fx, fy = J[ft]
            foot.addOval(skia.Rect(fx - 5 * s if f > 0 else fx - 17 * s, fy - 6 * s, fx + 17 * s if f > 0 else fx + 5 * s, fy + 3 * s))
            c.drawPath(foot, pt)
        # tronco + túnica/saia
        self._limb(c, J['hip'], J['sh'], wd['torso'] * s, pt)
        hx, hy = J['hip']; sx_, sy_ = J['sh']
        dx, dy = hx - sx_, hy - sy_; n = math.hypot(dx, dy) or 1; dx, dy = dx / n, dy / n; px, py = -dy, dx
        sk = skia.Path(); half = wd['torso'] * .5 * s; hem = (19 if not big else 36) * s; ln = (14 if not big else 30) * s
        flut = ex.get('flutter', 0) * s
        sk.moveTo(sx_ + px * half * .8, sy_ + py * half * .8)
        sk.lineTo(hx + dx * ln + px * hem + flut, hy + dy * ln + py * hem)
        for i in range(1, 6):
            u = i / 6
            sk.lineTo(hx + dx * (ln + math.sin(u * 9 + flut) * 3 * s) + px * lerp(hem, -hem, u) + flut * (1 - u),
                      hy + dy * ln + py * lerp(hem, -hem, u))
        sk.lineTo(hx + dx * ln - px * hem, hy + dy * ln - py * hem)
        sk.lineTo(sx_ - px * half * .8, sy_ - py * half * .8); sk.close()
        c.drawPath(sk, pt)
        if big:  # ombreiras
            c.drawCircle(sx_, sy_ + 4 * s, 22 * s, pt)
        # pescoço + cabeça
        self._limb(c, J['sh'], J['nk'], 10 * s * (1.5 if big else 1), pt)
        hx2, hy2 = J['hd']; r = self.L['head'] * s
        c.drawCircle(hx2, hy2, r, pt)
        nose = skia.Path(); nose.moveTo(hx2 + f * r * .8, hy2 - r * .2); nose.lineTo(hx2 + f * r * 1.25, hy2 + r * .15)
        nose.lineTo(hx2 + f * r * .7, hy2 + r * .4); nose.close(); c.drawPath(nose, pt)
        if big:
            hel = skia.Path(); hel.addArc(skia.Rect(hx2 - r * 1.15, hy2 - r * 1.35, hx2 + r * 1.15, hy2 + r * .6), 180, 180)
            c.drawPath(hel, pt)
            crest = skia.Path(); crest.moveTo(hx2 - f * r * .2, hy2 - r * 1.3)
            crest.quadTo(hx2 - f * r * 1.6, hy2 - r * 2.6, hx2 - f * r * 2.4, hy2 - r * .6)
            crest.lineTo(hx2 - f * r * 1.4, hy2 - r * 1.1); crest.close(); c.drawPath(crest, pt)
            beard = skia.Path(); beard.moveTo(hx2 - f * r * .4, hy2 + r * .2); beard.lineTo(hx2 + f * r * .9, hy2 + r * .5)
            beard.lineTo(hx2 + f * r * .1, hy2 + r * 1.7); beard.close(); c.drawPath(beard, pt)
        else:  # cabelo cacheado
            rr = random.Random(7)
            for i in range(9):
                a = math.radians(-200 + i * 26) if f > 0 else math.radians(20 - i * 26)
                c.drawCircle(hx2 + math.cos(a) * r * .9 - f * r * .15, hy2 + math.sin(a) * r * .9 - r * .1, r * rr.uniform(.38, .5), pt)
        # braço da frente
        self._limb(c, J['sh'], J['ef'], wd['arm'] * s, pt); self._limb(c, J['ef'], J['hf'], wd['arm'] * .9 * s, pt)
        c.drawCircle(J['hf'][0], J['hf'][1], wd['arm'] * .65 * s, pt)
        # acessórios
        if big and ex.get('spear', True):
            ex_, ey_ = J['ef']; hx3, hy3 = J['hf']; ang = ex.get('spear_angle')
            if ang is None:
                vx, vy = hx3 - ex_, hy3 - ey_
            else:
                vx, vy = math.sin(math.radians(ang)) * f, -math.cos(math.radians(ang))
            n = math.hypot(vx, vy) or 1; vx, vy = vx / n, vy / n
            a = (hx3 - vx * 150 * s, hy3 - vy * 150 * s); b = (hx3 + vx * 170 * s, hy3 + vy * 170 * s)
            self._limb(c, a, b, 6 * s, pt)
            tip = skia.Path(); tip.moveTo(b[0] + vx * 34 * s, b[1] + vy * 34 * s)
            tip.lineTo(b[0] - vy * 9 * s, b[1] + vx * 9 * s); tip.lineTo(b[0] + vy * 9 * s, b[1] - vx * 9 * s); tip.close()
            c.drawPath(tip, pt)
        if ex.get('staff'):
            hx3, hy3 = J['hb']; self._limb(c, (hx3, hy3 - 70 * s), (hx3 + f * 4 * s, hy3 + 95 * s), 5 * s, pt)
            hook = skia.Path(); hook.addArc(skia.Rect(hx3 - 4 * s, hy3 - 92 * s, hx3 + 22 * s * f if f > 0 else hx3 + 4 * s, hy3 - 64 * s), 180, 200)
        if ex.get('basket'):
            bx, by = J['hf']; c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(bx - 22 * s, by - 4 * s, bx + 22 * s, by + 26 * s), 8 * s, 8 * s), pt)
            for i in range(3): c.drawCircle(bx - 12 * s + i * 12 * s, by - 4 * s, 9 * s, pt)
        if ex.get('bag'):
            hx, hy = J['hip']; c.drawOval(skia.Rect(hx - f * 26 * s - 12 * s, hy - 4 * s, hx - f * 26 * s + 12 * s, hy + 20 * s), pt)
        if 'sling' in ex:
            hx3, hy3 = J['hf']; px_, py_ = ex['sling']
            q = skia.Paint(pt); q.setStyle(skia.Paint.kStroke_Style); q.setStrokeWidth(2.2 * s)
            c.drawLine(hx3, hy3, px_ - 4 * s, py_, q); c.drawLine(hx3, hy3, px_ + 4 * s, py_, q)
            c.drawOval(skia.Rect(px_ - 8 * s, py_ - 5 * s, px_ + 8 * s, py_ + 5 * s), pt)
        if ex.get('stone_in_hand'):
            hx3, hy3 = J['hf']; c.drawCircle(hx3 + f * 6 * s, hy3 - 4 * s, 6 * s, pt)

def soldier(c, x, ground, s, t, seed, color, arms_up=0.0, back=0.0, facing=1):
    """soldado simplificado (multidão)"""
    r = random.Random(seed); bob = math.sin(t * 2 + seed) * 1.5 * s
    fig = Figure('davi', s)
    p = pose(lean=r.uniform(-4, 4) - back * 10, head=r.uniform(-6, 6),
             ua_f=lerp(r.uniform(-5, 15), 175, arms_up), la_f=lerp(r.uniform(5, 25), 180, arms_up),
             ua_b=lerp(-8, -170, arms_up * r.uniform(.6, 1)), la_b=lerp(-4, -175, arms_up * .9),
             th_f=back * -14, sh_f=back * -20, th_b=back * 10, sh_b=back * 4)
    J = fig.draw(c, x, ground + bob, p, facing, color)
    if arms_up < .5:  # lança em pé
        hx, hy = J['hf']; c.drawLine(hx, hy + 30 * s, hx + facing * 3 * s, hy - 120 * s, paint(color, stroke=3.2 * s))
        tip = skia.Path(); tip.moveTo(hx + facing * 3 * s, hy - 138 * s); tip.lineTo(hx + facing * 3 * s - 5 * s, hy - 118 * s)
        tip.lineTo(hx + facing * 3 * s + 5 * s, hy - 118 * s); tip.close(); c.drawPath(tip, paint(color))
    c.drawCircle(J['hd'][0], J['hd'][1] - 3 * s, 15 * s, paint(color))  # capacete simples

# ---------------------------------------------------------------- acabamento
_grain = None
def finish(c, t, vignette=0.65, letter=0):
    global _grain
    vg = skia.GradientShader.MakeRadial((W / 2, H * .45), H * .78,
        [hexc('#000000', 0), hexc('#000000', 0), hexc('#000000', int(255 * vignette))], [0, .55, 1])
    c.drawRect(skia.Rect(0, 0, W, H), skia.Paint(Shader=vg))
    if _grain is None:
        rng = np.random.default_rng(3); _grain = []
        for i in range(6):
            g = rng.integers(0, 255, (H // 2, W // 2), dtype=np.uint8)
            rgba = np.dstack([g, g, g, np.full_like(g, 20)])
            _grain.append(skia.Image.fromarray(np.ascontiguousarray(rgba), colorType=skia.kRGBA_8888_ColorType))
    gi = _grain[int(t * FPS) % len(_grain)]
    p = skia.Paint(BlendMode=skia.BlendMode.kOverlay)
    c.drawImageRect(gi, skia.Rect(0, 0, W, H), skia.SamplingOptions(), p)
