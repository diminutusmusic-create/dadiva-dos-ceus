"""Miniatura + descrição/tags de um vídeo de louvores. Uso: python motor/meta_louvor.py louvores/<slug>.json"""
import json, os, sys, cv2, numpy as np, skia
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def miniatura(cen, l1, l2, l3, l4, saida):
    img = cv2.resize(cv2.imread(f'{RAIZ}/arte/paisagens/{cen}.png'), (1280, 720), interpolation=cv2.INTER_LANCZOS4)
    x = np.linspace(0, 1, 1280)[None, :, None]; y = np.linspace(0, 1, 720)[:, None, None]
    img = (img * np.clip(1 - .62 * np.clip(1.15 - x * 1.6, 0, 1), .38, 1) * (1 - .25 * y)).astype(np.uint8)
    rgba = cv2.cvtColor(img, cv2.COLOR_BGR2RGBA); s = skia.Surface(rgba)
    F = lambda n, t: skia.Font(skia.Typeface.MakeFromFile(f'{RAIZ}/fontes/{n}.ttf'), t)
    def txt(c, t, x, y, f, cor):
        c.drawString(t, x + 3, y + 4, f, skia.Paint(AntiAlias=True, Color=skia.Color(0, 0, 0, 200), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 10)))
        c.drawString(t, x, y, f, skia.Paint(AntiAlias=True, Color=cor))
    with s as c:
        tam = 150
        while F('Cinzel-Bold', tam).measureText(l1.upper()) > 1120: tam -= 6
        txt(c, l1.upper(), 70, 300, F('Cinzel-Bold', tam), skia.Color(255, 240, 205))
        txt(c, l2, 78, 385, F('Cormorant-Bold', 64), skia.Color(255, 250, 240))
        txt(c, l3, 80, 470, F('Cinzel-Bold', 46), skia.Color(240, 200, 120))
        txt(c, l4, 82, 525, F('Cormorant-Medium', 40), skia.Color(235, 225, 205))
    cv2.imwrite(saida, cv2.cvtColor(rgba, cv2.COLOR_RGBA2BGR), [cv2.IMWRITE_JPEG_QUALITY, 90])

def gerar(cam):
    R = json.load(open(cam)); slug = os.path.basename(cam)[:-5]; M = R['meta']
    caps = json.load(open(f'{RAIZ}/louvores/{slug}.capitulos.json'))
    linhas = [f"{t} {n}" for t, n in caps]
    refs = " · ".join(f"{f['titulo']} ({f['ref']})" for f in R['faixas'])
    desc = (M['intro'] + "\n\nPara orar, descansar, trabalhar, estudar ou adormecer na presença de Deus. 🎶\n\n"
            "⏱️ Louvores\n" + "\n".join(linhas) + "\n\n📖 Inspirados em: " + refs +
            "\n\n🙏 Deixe nos comentários qual louvor mais tocou o seu coração, ou um pedido de oração.\n\n"
            "🔔 Inscreva-se no Dádiva dos Céus para novos louvores, leituras e histórias da Bíblia.\n\n"
            "Letras originais inspiradas nas Escrituras, músicas e vozes geradas com auxílio de IA (Treblo). "
            "Textos bíblicos: Bíblia Livre (BLIVRE), licença Creative Commons Atribuição 4.0 Brasil.\n\n#louvor #musicagospel #louvoresparaorar")
    miniatura(M['cenario'], M['l1'], M['l2'], M['l3'], M['l4'], f'{RAIZ}/marca/miniaturas/{slug}.jpg')
    json.dump({'titulo': M['titulo'], 'descricao': desc, 'tags': M['tags']}, open(f'{RAIZ}/louvores/{slug}.youtube.json', 'w'), ensure_ascii=False, indent=1)
    print(M['titulo'], len(desc), sum(len(t) + 1 for t in M['tags']))

if __name__ == '__main__': gerar(sys.argv[1])
