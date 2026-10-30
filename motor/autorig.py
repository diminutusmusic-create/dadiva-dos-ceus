"""Detecta olhos, boca e pescoço de um personagem cartoon (fundo branco) para animar piscada e fala."""
import numpy as np
from PIL import Image
from scipy import ndimage
from cartoon_rig import cutout

def hexc(rgb): return '#%02x%02x%02x' % tuple(int(v) for v in rgb)

def autorig(path):
    rgba = cutout(path); im = rgba[..., :3].astype(int); a = rgba[..., 3] > 128
    ys, xs = np.where(a); top, bot = ys.min(), ys.max(); hgt = bot - top
    cx = (xs.min() + xs.max()) / 2
    y0, y1 = top, top + int(hgt * .42)
    dark = (im.max(2) < 95) & a
    dark[:y0] = False; dark[y1:] = False
    lab, n = ndimage.label(dark)
    cands = []
    for i, sl in enumerate(ndimage.find_objects(lab), 1):
        h = sl[0].stop - sl[0].start; w = sl[1].stop - sl[1].start
        area = (lab[sl] == i).sum()
        if 30 < area < 2500 and .45 < h / max(w, 1) < 2.6 and area / (h * w) > .55:
            cands.append(((sl[1].start + sl[1].stop) / 2, (sl[0].start + sl[0].stop) / 2, w, h, area))
    best = None
    for i in range(len(cands)):
        for j in range(i + 1, len(cands)):
            A, B = cands[i], cands[j]
            if A[0] > B[0]: A, B = B, A
            d = B[0] - A[0]
            if not (35 < d < 170): continue
            sc = abs(A[1] - B[1]) * 3 + abs((A[0] + B[0]) / 2 - cx) + abs(A[4] - B[4]) / 20 + abs(A[2] - B[2]) * 2
            if best is None or sc < best[0]: best = (sc, A, B)
    if best is None or best[0] > 60: return None
    _, A, B = best
    d = B[0] - A[0]; ey = (A[1] + B[1]) / 2; mid = (A[0] + B[0]) / 2
    rx = max(A[2], B[2]) / 2 + 5; ry = max(A[3], B[3]) / 2 + 6
    skin = np.median(im[int(ey) - 2:int(ey) + 3, int(mid) - 3:int(mid) + 4].reshape(-1, 3), 0)
    my = int(ey + .52 * d)  # proporção típica do rosto chibi gerado
    beard = np.median(im[my - 2:my + 3, int(mid - .42 * d):int(mid - .32 * d)].reshape(-1, 3), 0)
    neck = int(ey + 1.05 * d)
    return dict(neck_y=neck, neck_pivot=(int(mid), neck + 8), feather=14,
                eyes=[(int(A[0]), int(A[1])), (int(B[0]), int(B[1]))], eye_r=(int(rx), int(ry)),
                mouth=(int(mid), my + 2), mouth_w=int(d * .42), mouth_patch=(int(d * .4), int(d * .2)),
                skin=hexc(skin), beard=hexc(beard), line='#3b1d10')
