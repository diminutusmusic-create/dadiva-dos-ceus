# Acrescenta uma cena final original (aplicação + oração/versículo/desafio) aos Shorts da semana 1,
# para cumprir a regra de 95s+ de todas as plataformas. Finais variados para não parecer molde.
import json, glob, copy, sys
N = 'narrador'
EXT = {
'008': [(N,"Repare numa coisa: | o pai não ficou esperando o filho chegar até a porta. | Ele correu. | Naquele tempo, | um homem respeitado não corria. | Mas o amor falou mais alto que o orgulho."),
        (N,"Talvez você esteja longe hoje. | Longe de casa, | longe de Deus, | longe de quem você era. | E acha que já foi longe demais para voltar."),
        (N,"Então ore comigo: | Pai, | eu voltei. | Não mereço, | mas preciso do teu abraço. | Me recebe de novo. | Amém.")],
'003': [(N,"Noé passou anos construindo | sem ver uma gota de chuva. | Todo dia, | alguém dizia que ele estava louco. | E todo dia, | ele pegava a ferramenta | e continuava."),
        (N,"Depois do dilúvio, | Deus colocou o arco-íris no céu | como sinal de uma aliança | que nunca seria quebrada."),
        (N,"Guarde este versículo: | Gênesis nove, treze. | Ponho o meu arco nas nuvens, | e ele será o sinal da aliança. | Toda vez que você vir um arco-íris, | lembre: | Deus cumpre o que promete.")],
'009': [(N,"Zaqueu não ganhou um sermão. | Ganhou um convite. | E foi o convite | que fez ele querer mudar."),
        (N,"Ele não esperou ninguém mandar. | Na mesma hora, | decidiu devolver o que tinha tirado | e ajudar quem precisava. | Fé de verdade | mexe no bolso, | no coração | e nas atitudes."),
        (N,"Fica um desafio para hoje: | pense em alguém que todo mundo já desistiu. | Faça como Jesus. | Chame essa pessoa pelo nome, | mande uma mensagem, | ofereça um café. | Um encontro pode mudar uma vida inteira.")],
'004': [(N,"O mais incrível dessa história | não é o peixe. | É que Deus deu a Jonas | uma segunda chance. | E depois, | deu uma chance para Nínive também."),
        (N,"Jonas achava que algumas pessoas | não mereciam o perdão de Deus. | Mas Deus olhou para aquela cidade inteira | com compaixão."),
        (N,"E você? | Está fugindo de alguma coisa | que Deus pediu? | Ore comigo: | Senhor, | eu paro de fugir. | Me dá coragem para obedecer, | e um coração como o teu. | Amém.")],
'010': [(N,"Os discípulos conheciam aquele lago. | Mas naquela noite, | a experiência deles não foi suficiente. | Às vezes, | Deus permite uma tempestade | para nos mostrar quem Ele é."),
        (N,"E repare: | Jesus estava no barco o tempo todo. | Dormindo, | mas presente. | O silêncio de Deus | não é ausência de Deus."),
        (N,"Guarde esta promessa: | Isaías quarenta e três, dois. | Quando você passar pelas águas, | eu estarei com você. | Seja qual for a sua tempestade hoje, | Ele está no barco.")],
'005': [(N,"Daniel poderia ter orado escondido. | Ou parado só por trinta dias. | Mas ele preferiu manter a janela aberta. | A fidelidade dele | não dependia das circunstâncias."),
        (N,"E foi justamente essa fidelidade | que fez um rei pagão | reconhecer o Deus vivo. | A vida de Daniel pregou | sem ele dizer uma palavra."),
        (N,"Fica um desafio: | escolha um horário fixo para orar amanhã. | Pode ser cinco minutos. | Abra a sua janela, | como Daniel. | Quem conversa com Deus todos os dias | não enfrenta nada sozinho.")],
'011': [(N,"Pedro foi o único | que saiu do barco. | Os outros ficaram olhando. | Ele afundou, | é verdade. | Mas também foi o único | que andou sobre as águas."),
        (N,"E quando ele gritou, | Jesus não demorou. | Estendeu a mão na mesma hora. | Não deixou Pedro afundar | por ter tido medo."),
        (N,"Ore comigo: | Senhor, | eu quero sair do barco. | Quando o vento me assustar, | segura a minha mão. | Que os meus olhos fiquem em ti. | Amém.")],
'006': [(N,"Antes do mar se abrir, | o povo precisou ficar parado | diante do impossível. | Encurralado, | sem plano, | sem saída."),
        (N,"Foi ali que Moisés disse uma das frases | mais fortes da Bíblia. | O Senhor lutará por vocês. | Vocês só precisam ficar em paz."),
        (N,"Guarde este versículo: | Êxodo catorze, catorze. | O Senhor pelejará por vós, | e vós vos calareis. | Se hoje você está entre o mar e o exército, | respire. | Deus ainda abre caminhos.")],
'012': [(N,"Jesus podia ter feito pão cair do céu. | Mas escolheu usar o lanche de um menino. | Ele gosta de multiplicar | aquilo que a gente entrega."),
        (N,"E repare: | sobraram doze cestos. | Deus não dá na medida certa. | Ele dá com fartura. | E Jesus ainda mandou recolher tudo, | porque nada do que vem de Deus | é desperdício."),
        (N,"Fica um desafio para hoje: | divida alguma coisa. | Uma refeição, | uma palavra, | o seu tempo. | Pode parecer pouco. | Mas entregue nas mãos de Jesus, | o seu pouco pode alimentar muita gente.")],
'013': [(N,"José passou mais de dez anos | entre o poço e o palácio. | Escravo, | preso, | esquecido. | E em nenhum momento | deixou de ser fiel."),
        (N,"Quando finalmente teve poder, | podia ter se vingado dos irmãos. | Mas escolheu perdoar. | E salvou a própria família da fome."),
        (N,"Guarde este versículo: | Romanos oito, vinte e oito. | Todas as coisas cooperam para o bem | daqueles que amam a Deus. | O que hoje parece um poço | pode ser o caminho para o seu palácio.")],
'015': [(N,"Jesus não disse: | venham a mim os fortes. | Nem: | venham os que já estão bem. | Ele chamou os cansados. | Os sobrecarregados."),
        (N,"Então, agora, | faça uma pausa. | Respire fundo. | Solte os ombros. | E entregue o peso que você está carregando."),
        (N,"Ore comigo: | Jesus, | eu estou cansado. | Eu entrego a ti | o que eu não consigo mais carregar. | Me dá o teu descanso. | Amém.")],
'014': [(N,"Rute não tinha nada a ganhar | ficando com Noemi. | Era estrangeira, | viúva | e pobre. | Mesmo assim, | escolheu ser leal."),
        (N,"E Deus honrou essa escolha | de um jeito que ninguém imaginaria. | Rute se tornou bisavó do rei Davi. | E entrou para a família de Jesus."),
        (N,"Pense agora: | quem é a sua Noemi? | Quem precisa da sua lealdade hoje? | Como diz Provérbios: | o amigo ama em todo tempo. | Seja esse amigo para alguém.")],
}
for k, falas in EXT.items():
    p = glob.glob(f'/home/claude/dadiva-dos-ceus/roteiros/{k}-*.json')[0]
    r = json.load(open(p, encoding='utf-8'))
    if r.get('estendido'): continue
    nova = copy.deepcopy(r['cenas'][-1]); nova['falas'] = [dict(quem=q, texto=t) for q, t in falas]
    nova['efeito'] = ['luz']
    r['cenas'].append(nova); r['estendido'] = True
    json.dump(r, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    print('ok', p)
