"""Gera capítulos, descrição, tags e miniatura de um vídeo de leitura.
Uso: python motor/meta_longo.py <slug> "<título YouTube>" "<linha 1 miniatura>" "<linha 2>" <cenario_miniatura> "<tags,separadas>" "<intro>"
"""
import json, os, sys, pickle, hashlib, re
import cv2, numpy as np, skia
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from leitura import SR
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def capitulos(slug):
    R = json.load(open(f'{RAIZ}/leituras/{slug}.json'))
    its = [(bi, it) for bi, b in enumerate(R['blocos']) for it in b['itens']]
    tx = [it['texto'] for _, it in its if it['tipo'] != 'silencio']
    ck = f"/tmp/tts_{hashlib.md5(json.dumps([tx, R['voz'], R['velocidade']]).encode()).hexdigest()}.pkl"
    au = pickle.load(open(ck, 'rb')); t = 7.0; ini = {}
    for (bi, it), a in zip(its, au):
        ini.setdefault(bi, t); t += len(a) / SR + it.get('pausa', 2.4)
    caps = []
    for bi, b in enumerate(R['blocos']):
        s = 0 if bi == 0 else max(0, ini[bi] - 1.5)
        caps.append(f"{int(s // 60)}:{int(s % 60):02d} {b.get('nome', '')}")
    refs = []
    for b in R['blocos']:
        for it in b['itens']:
            if it['tipo'] == 'verso':
                livro_cap = it['ref'].rsplit(':', 1)[0]
                if livro_cap not in refs: refs.append(livro_cap)
    return caps, refs

def miniatura(cen, l1, l2, saida):
    img = cv2.imread(f'{RAIZ}/arte/paisagens/{cen}.png'); img = cv2.resize(img, (1280, 720), interpolation=cv2.INTER_LANCZOS4)
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
        txt(c, 'PARA DORMIR EM PAZ', 80, 470, F('Cinzel-Bold', 46), skia.Color(240, 200, 120))
        txt(c, 'meditação · oração da noite', 82, 525, F('Cormorant-Medium', 40), skia.Color(235, 225, 205))
    cv2.imwrite(saida, cv2.cvtColor(rgba, cv2.COLOR_RGBA2BGR), [cv2.IMWRITE_JPEG_QUALITY, 90])

def gerar(slug, titulo, l1, l2, cen, tags, intro):
    caps, refs = capitulos(slug)
    desc = (intro + "\n\nIdeal para ouvir antes de dormir, em momentos de ansiedade, ou para terminar o dia com a Palavra de Deus. 🌙\n\n"
            "📖 Passagens deste vídeo:\n" + " · ".join(refs) + "\n\n⏱️ Capítulos\n" + "\n".join(caps) +
            "\n\n🙏 Se este vídeo abençoou você, deixe nos comentários um pedido de oração ou uma palavra de gratidão. Vamos orar juntos.\n\n"
            "🔔 Inscreva-se no Dádiva dos Céus e ative o sininho para receber novas leituras, orações e histórias da Bíblia.\n\n"
            "Textos bíblicos: Bíblia Livre (BLIVRE), © Diego Santos, Mario Sérgio e Marco Teles, licença Creative Commons Atribuição 4.0 Brasil "
            "(creativecommons.org/licenses/by/4.0/br). Narração, meditações e trilha: Dádiva dos Céus.\n\n#oraçãodanoite #bibliaparadormir #palavradedeus")
    tl = [t.strip() for t in tags.split(',') if t.strip()]
    os.makedirs(f'{RAIZ}/marca/miniaturas', exist_ok=True)
    miniatura(cen, l1, l2, f'{RAIZ}/marca/miniaturas/{slug}.jpg')
    json.dump({'titulo': titulo, 'descricao': desc, 'tags': tl}, open(f'{RAIZ}/leituras/{slug}.youtube.json', 'w'), ensure_ascii=False, indent=1)
    print(titulo, len(desc), sum(len(t) + 1 for t in tl))

if __name__ == '__main__':
    gerar(*sys.argv[1:8])
