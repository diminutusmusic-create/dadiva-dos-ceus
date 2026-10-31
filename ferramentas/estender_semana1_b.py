# Segunda camada: um trecho de contexto na história (cena do meio), para chegar a ~100s sem silêncio.
import json, glob
N='narrador'
MEIO = {
'008': "Pedir a herança com o pai ainda vivo | era como dizer: | para mim, você já morreu. | Mesmo assim, | o pai dividiu tudo | e deixou o filho partir. | E todos os dias, | olhava para a estrada.",
'003': "Enquanto Noé martelava, | a vida seguia normal para todo mundo. | Festas, | casamentos, | negócios. | Ninguém achava que precisava de uma arca. | Até que a primeira gota caiu.",
'009': "Os cobradores de impostos trabalhavam para Roma | e eram vistos como traidores do próprio povo. | Ninguém se sentava à mesa com eles. | Zaqueu tinha dinheiro, | mas não tinha amigos.",
'004': "Jonas pegou um navio para o lado oposto. | Mas no meio do mar, | veio uma tempestade tão forte | que os marinheiros acharam que iam morrer. | E Jonas sabia que a culpa era dele.",
'010': "O lago da Galileia fica entre montanhas. | O vento desce de repente pelos vales | e transforma a água calma | em ondas enormes | em poucos minutos.",
'005': "Daniel já era idoso. | Tinha servido a vários reis | e nunca tinham encontrado nenhum erro nele. | Por isso, | a única forma de acusá-lo | era pela sua fé.",
'011': "Era madrugada. | Os discípulos remavam havia horas | contra um vento forte. | Estavam cansados, | molhados | e longe da margem. | Foi aí que viram alguém | caminhando sobre as águas.",
'006': "Deus guiava o povo de um jeito impressionante: | de dia, | uma coluna de nuvem. | De noite, | uma coluna de fogo. | E naquela noite, | a nuvem ficou entre o povo e o exército.",
'012': "Os discípulos já tinham feito as contas. | A solução deles era simples: | mandar todo mundo embora. | Mas Jesus tinha outra ideia. | Ele queria que eles vissem | o que Deus faz com o pouco.",
'013': "Na prisão, | José ajudou dois homens do faraó | a entender seus sonhos. | Um deles prometeu se lembrar de José | quando saísse. | E esqueceu. | Por mais dois anos.",
'015': "Jesus falava para pessoas | carregadas de regras, | cobranças | e culpa. | Gente que trabalhava muito | e mesmo assim sentia | que nunca era suficiente para Deus.",
'014': "Naquele tempo, | uma viúva sem filhos | não tinha quem a sustentasse. | Ficar com Noemi | significava escolher a pobreza | e uma terra estranha. | Rute escolheu mesmo assim.",
}
# Shorts ainda curtos depois da 1ª camada ganham também uma fala extra no fim da história
for k, t in MEIO.items():
    p = glob.glob(f'/home/claude/dadiva-dos-ceus/roteiros/{k}-*.json')[0]
    r = json.load(open(p, encoding='utf-8'))
    if r.get('estendido_b'): continue
    r['cenas'][1]['falas'].append(dict(quem=N, texto=t)); r['estendido_b'] = True
    json.dump(r, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print('ok')
