"""Converte um roteiro em texto (DSL simples) no JSON do motor de leitura + .md para aprovação.

Formato do .txt:
    # Título | Subtítulo
    ## Nome da seção | cenario | efeito1,efeito2 | Rótulo na tela
    > PSA091:1-4          (versículos da Bíblia Livre, mostrados na tela)
    Texto de narração (cada linha é uma fala).
Uso: python leituras/montar.py leituras/roteiros/salmo-91.txt
"""
import json, os, re, sys
AQUI = os.path.dirname(os.path.abspath(__file__))
T = json.load(open(f'{AQUI}/blivre.json'))
LIVROS = {'PSA': 'Salmo', 'MAT': 'Mateus', 'JHN': 'João', 'PRO': 'Provérbios', 'ISA': 'Isaías', 'ROM': 'Romanos',
          'REV': 'Apocalipse', 'JER': 'Jeremias', 'EPH': 'Efésios', 'PHP': 'Filipenses', '1PE': '1 Pedro',
          'LAM': 'Lamentações', 'MIC': 'Miqueias', '2CO': '2 Coríntios', 'MAT11': 'Mateus'}

def versos(spec, pausa):
    m = re.match(r'([0-9A-Z]{3})(\d+):(\d+)(?:-(\d+))?', spec.strip())
    liv, cap, a, b = m.group(1), m.group(2), int(m.group(3)), int(m.group(4) or m.group(3))
    out = []
    for v in range(a, b + 1):
        out.append({'tipo': 'verso', 'ref': f'{LIVROS[liv]} {int(cap)}:{v}', 'texto': T[f'{liv}{cap}:{v}'], 'pausa': pausa})
    out[-1]['pausa'] = pausa + .6
    return out

def montar(caminho):
    linhas = open(caminho, encoding='utf-8').read().split('\n')
    titulo, sub = [x.strip() for x in linhas[0].lstrip('# ').split('|')]
    blocos, md = [], [f'# {titulo} — {sub}\n', 'Textos bíblicos: Bíblia Livre (BLIVRE), CC BY 4.0. Meditações e orações: texto original do canal.\n']
    for ln in linhas[1:]:
        ln = ln.strip()
        if not ln: continue
        if ln.startswith('## '):
            nome, cen, ef, rot = [x.strip() for x in ln[3:].split('|')]
            blocos.append({'nome': nome, 'cenario': cen, 'efeito': [e for e in ef.split(',') if e], 'rotulo': rot, 'itens': []})
            md.append(f'\n## {nome}\n')
        elif ln.startswith('>'):
            vs = versos(ln[1:], 2.6)
            blocos[-1]['itens'] += vs
            md += [f"> **{v['ref']}** — {v['texto']}\n" for v in vs]
        else:
            blocos[-1]['itens'].append({'tipo': 'fala', 'texto': ln, 'rotulo': blocos[-1]['rotulo'], 'pausa': 1.3})
            md.append(ln + '\n')
    for b in blocos: b['itens'][-1]['pausa'] = max(b['itens'][-1]['pausa'], 4.0)
    slug = os.path.splitext(os.path.basename(caminho))[0]
    R = {'titulo': titulo, 'subtitulo': sub, 'voz': 'pm_santa', 'velocidade': 1.0, 'pausa_verso': 2.4,
         'ambiente': 'riacho', 'fps': 24, 'cauda': 20, 'fim': 'Dádiva dos Céus', 'blocos': blocos}
    json.dump(R, open(f'{AQUI}/{slug}.json', 'w'), ensure_ascii=False, indent=1)
    open(f'{AQUI}/roteiros/{slug}.md', 'w').write('\n'.join(md))
    pal = sum(len(it['texto'].split()) for b in blocos for it in b['itens'])
    print(slug, 'palavras', pal, '≈ min', round(pal / 146 + sum(it['pausa'] for b in blocos for it in b['itens']) / 60, 1))
    return R

if __name__ == '__main__':
    for c in sys.argv[1:]: montar(c)
