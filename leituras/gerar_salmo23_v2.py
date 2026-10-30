"""Roteiro v2 do Salmo 23 (narração contínua ~28 min). Gera o .json para o motor e o .md para aprovação."""
import json, os
AQUI = os.path.dirname(os.path.abspath(__file__))

S23 = ["O SENHOR é meu pastor, nada me faltará.",
 "Ele me faz deitar em pastos verdes, e me leva a águas quietas.",
 "Ele restaura minha alma, e me guia pelos caminhos da justiça por seu nome.",
 "Ainda que eu venha a andar pelo vale da sombra da morte, não temerei mal algum, porque tu estás comigo; tua vara e teu cajado me consolam.",
 "Tu preparas uma mesa diante de mim à vista de meus adversários; unges a minha cabeça com azeite, meu cálice transborda.",
 "Certamente o bem e a bondade me seguirão todos os dias de minha vida; e habitarei na casa do SENHOR por muitos e muitos dias."]

def V(ref, txt, pausa=2.2): return {'tipo': 'verso', 'ref': ref, 'texto': txt, 'pausa': pausa}
def F(txt, rot, pausa=1.3): return {'tipo': 'fala', 'texto': txt, 'rotulo': rot, 'pausa': pausa}
def falas(bloco, rot): return [F(p.strip(), rot) for p in bloco.strip().split('\n') if p.strip()]

SEC = []  # (titulo, cenario, efeitos, itens)

SEC.append(("Abertura", 'lago_nevoa', ['nevoa'], falas("""
Seja bem-vindo. Que bom que você está aqui.
Este é um momento para desacelerar. O dia já fez o que tinha que fazer. Agora é hora de descansar.
Se puder, ajeite o corpo com calma. Solte os ombros. Deixe as mãos descansarem.
Respire fundo, devagar… e deixe o ar sair sem pressa. Mais uma vez. Inspire… e solte.
Nos próximos minutos, vamos caminhar juntos por um dos textos mais conhecidos e mais amados de toda a Bíblia: o Salmo vinte e três.
Muitas pessoas aprenderam esse salmo ainda crianças. Outras o repetiram em hospitais, em despedidas, em noites de insônia. Ele atravessou três mil anos e continua chegando ao coração de quem precisa de paz.
Vamos ler o salmo inteiro primeiro. Depois, vamos voltar a cada versículo com calma, e ouvir também outras passagens das Escrituras que falam do mesmo Pastor.
Não é preciso fazer nada. Apenas ouça. E se o sono chegar no meio do caminho, receba-o como um presente.
""", "Abertura")))

SEC.append(("Leitura do Salmo 23", 'galileia_amanhecer', ['poeira'],
            [V(f"Salmo 23:{i+1}", t, 2.6) for i, t in enumerate(S23)]))

SEC.append(("O pastor que escreveu o salmo", 'pastos_amanhecer', ['nevoa', 'poeira'], falas("""
Antes de ser rei, Davi foi pastor.
Ele era o filho mais novo de Jessé, em Belém. Enquanto os irmãos mais velhos iam para a guerra, Davi ficava no campo, cuidando das ovelhas do pai.
Era um trabalho simples, e muitas vezes solitário. Dias inteiros sob o sol, noites frias olhando as estrelas, procurando água e pasto em uma terra seca e cheia de pedras.
Davi conhecia cada ovelha. Sabia qual mancava, qual se afastava do grupo, qual tinha medo à noite.
E ele sabia também dos perigos. A Bíblia conta que, para proteger o rebanho, Davi enfrentou um leão e um urso.
Por isso, quando Davi escreve "o Senhor é o meu pastor", ele não está usando uma imagem bonita qualquer. Ele está falando de algo que conhece por dentro.
É como se dissesse: eu sei o que um pastor faz por suas ovelhas. Eu sei o cuidado, a atenção, a coragem que isso exige. E é exatamente assim que Deus cuida de mim.
Repare também que Davi não diz "o Senhor é um pastor", ou "o pastor de Israel". Ele diz: "o meu pastor".
É uma relação pessoal. Próxima. Esta noite, você também pode dizer essas palavras como suas.
""", "O pastor Davi")))

SEC.append(("Versículos 1 e 2", 'aguas_quietas', ['poeira'],
 [V("Salmo 23:1", S23[0], 2.8)] + falas("""
"Nada me faltará." Talvez essa seja uma das frases mais difíceis de acreditar quando a vida aperta.
Porque às vezes falta. Falta dinheiro no fim do mês. Falta saúde. Falta alguém que já não está mais conosco. Falta paciência, falta força.
Mas Davi não está prometendo uma vida sem falta de nada. Ele está dizendo outra coisa: que, com esse Pastor, não vai faltar o que é essencial.
Não vai faltar cuidado. Não vai faltar direção. Não vai faltar presença.
As ovelhas não carregam a preocupação com o pasto de amanhã. Elas seguem quem conhece o caminho.
""", "Meditação · Salmo 23:1") + [V("Salmo 23:2", S23[1], 2.8)] + falas("""
Os pastores contam que uma ovelha só se deita quando se sente segura. Se tem medo, se está com fome, se há tensão no rebanho, ela não descansa.
Por isso o salmo diz: Ele me faz deitar. É o Pastor quem cria as condições para o descanso. Ele afasta o perigo, encontra o pasto, acalma o rebanho.
E repare nas águas. Não são águas agitadas, de correnteza forte, onde a ovelha poderia ser arrastada. São águas quietas. Tranquilas. Seguras para beber.
Muitas vezes a nossa mente é como uma correnteza. Pensamentos que não param, conversas que repetimos por dentro, preocupações que voltam sempre.
Esta noite, imagine que o Pastor conduz você até a beira dessa água calma. Não há pressa. Não há cobrança. Só o som da água e a grama macia.
Você tem permissão para parar. Você tem permissão para descansar.
""", "Meditação · Salmo 23:2")))

SEC.append(("Versículo 3", 'caminho_oliveiras', ['poeira'],
 [V("Salmo 23:3", S23[2], 2.8)] + falas("""
"Ele restaura minha alma." Restaurar é devolver algo ao estado em que deveria estar.
Um móvel antigo é restaurado. Uma pintura gasta é restaurada. E uma alma cansada também pode ser restaurada.
Há um cansaço que o sono resolve. Mas há outro cansaço, mais fundo, que não passa com uma noite de descanso. É o cansaço da alma. A tristeza que pesa, a culpa que não sai, a esperança que foi se apagando aos poucos.
Esse tipo de cansaço nós não conseguimos consertar sozinhos. E a boa notícia do salmo é que não precisamos. É Ele quem restaura.
Depois, o versículo fala em caminhos. Ele me guia pelos caminhos da justiça. Caminhos certos, retos, que levam a algum lugar bom.
Nem sempre enxergamos o caminho inteiro. Às vezes só vemos o próximo passo. Mas a ovelha não precisa ver o mapa. Ela só precisa seguir o pastor.
E por que Ele faz isso? "Por seu nome." Não porque merecemos, mas porque é da natureza dEle cuidar. Ele é fiel ao próprio nome.
""", "Meditação · Salmo 23:3")))

SEC.append(("Versículo 4", 'vale_sombra', ['nevoa'],
 [V("Salmo 23:4", S23[3], 3.0)] + falas("""
Este é o centro do salmo. E é também o versículo que mais pessoas guardam no coração.
Repare que o salmo não esconde a realidade. Ele não diz "eu nunca vou passar por um vale escuro". Ele diz: ainda que eu venha a andar por ele.
Os vales existem. Há perdas, diagnósticos, noites longas, períodos em que tudo parece sombra.
Na terra de Israel, havia vales estreitos e profundos entre os montes, onde a luz do sol quase não chegava. Os pastores precisavam atravessá-los para levar o rebanho de um pasto a outro. Eram lugares perigosos, mas eram caminho. Não eram o destino.
Há algo muito bonito escondido neste versículo. Até aqui, Davi falava de Deus na terceira pessoa: "Ele me faz deitar", "Ele restaura", "Ele me guia".
Mas quando chega ao vale escuro, a linguagem muda. Ele não fala mais "Ele". Ele fala "tu". "Porque tu estás comigo."
É no lugar mais escuro que a conversa fica mais próxima. É ali que Deus deixa de ser assunto e passa a ser companhia.
E então aparecem a vara e o cajado. A vara era usada para afastar os animais que ameaçavam o rebanho. O cajado, com a ponta curva, servia para puxar a ovelha que caía em um buraco, ou guiá-la de volta para perto.
Proteção e direção. É isso que consola.
Se você está atravessando um vale neste tempo da sua vida, ouça de novo: tu estás comigo. Você não atravessa sozinho.
""", "Meditação · Salmo 23:4")))

SEC.append(("Versículos 5 e 6", 'lamparina_mesa', ['poeira'],
 [V("Salmo 23:5", S23[4], 2.8)] + falas("""
Agora a cena muda. O campo dá lugar a uma casa, e o pastor se torna anfitrião.
No mundo de Davi, receber alguém à mesa era um sinal de proteção. Quem comia sob o seu teto estava seguro.
E Deus prepara essa mesa "à vista dos adversários". Os problemas não desaparecem de repente. Mas, mesmo com eles ao redor, há um lugar de paz preparado para você.
Ungir a cabeça com azeite era um gesto de honra e de carinho. Era assim que se recebia um convidado querido, depois de uma longa viagem.
E o cálice não fica só cheio. Ele transborda. A bondade de Deus é sempre maior do que a medida que esperamos.
""", "Meditação · Salmo 23:5") + [V("Salmo 23:6", S23[5], 2.8)] + falas("""
O salmo termina com uma palavra firme: certamente. Não é talvez. Não é se tudo der certo. É certamente.
E veja o verbo: o bem e a bondade me seguirão. Na língua original, a ideia é ainda mais forte. É como se a bondade de Deus perseguisse você. Corresse atrás, não deixasse você escapar.
Todos os dias. Nos dias bons e nos dias difíceis. Nos dias em que você sente essa bondade, e também nos dias em que não sente nada.
E o destino final é a casa do Senhor. Um lar. Um lugar de pertencimento, onde ninguém é visita, porque todos são filhos.
""", "Meditação · Salmo 23:6")))

SEC.append(("Isaías 40", 'cedros_montanha', ['nevoa'],
 falas("""
O Salmo vinte e três não é o único lugar da Bíblia onde Deus aparece como pastor. Essa imagem atravessa as Escrituras do começo ao fim.
Séculos depois de Davi, o profeta Isaías escreveu ao povo de Israel em um tempo de exílio e cansaço. E ele trouxe esta promessa:
""", "Isaías 40") + [V("Isaías 40:11", "Como pastor ele apascentará seu rebanho; em seus braços recolherá aos cordeirinhos, e os levará em seu colo; ele guiará mansamente as que tiveram filhotes.", 3.0)] + falas("""
Que imagem delicada. O Deus que criou as estrelas pega os cordeirinhos no colo.
Ele conhece quem está fraco, quem está cansado, quem carrega mais peso do que consegue. E ele guia essas ovelhas com mansidão, no ritmo delas.
Se esta noite você se sente pequeno, ou frágil, saiba que é justamente para esses que Ele estende os braços primeiro.
""", "Meditação · Isaías 40:11")))

SEC.append(("Ezequiel 34", 'jerusalem_entardecer', [],
 falas("""
O profeta Ezequiel também falou de pastores. Naquele tempo, os líderes do povo tinham abandonado o rebanho. Cuidavam de si mesmos, e as ovelhas estavam espalhadas.
Então Deus fez uma promessa: Ele mesmo iria cuidar das suas ovelhas.
""", "Ezequiel 34") + [V("Ezequiel 34:11", "Porque assim diz o Senhor DEUS: Eis que eu, eu mesmo, procurarei minhas ovelhas, e as buscarei.", 2.4),
 V("Ezequiel 34:15", "Eu apascentarei minhas ovelhas, e eu farei elas se deitarem em segurança, diz o Senhor DEUS.", 2.4),
 V("Ezequiel 34:16", "Eu buscarei a perdida, e trarei de volta a desgarrada; porei curativo na que estiver ferida, e fortalecerei a enferma.", 3.0)] + falas("""
Eu mesmo. Deus não delega esse cuidado. Ele vem pessoalmente.
E veja a lista: a perdida, a desgarrada, a ferida, a fraca. Não são as ovelhas fortes e bonitas que recebem atenção especial. São as que mais precisam.
Talvez você se reconheça em alguma delas. Perdido, ferido, sem forças. Esta promessa também é para você: Ele busca, Ele traz de volta, Ele faz o curativo.
""", "Meditação · Ezequiel 34")))

SEC.append(("Lucas 15", 'trigo_chuva', ['nevoa'],
 falas("""
Quando Jesus veio, Ele contou uma história que mostra até onde vai o cuidado desse Pastor.
""", "Lucas 15") + [V("Lucas 15:4", "Quem de vós, tendo cem ovelhas, e perdendo uma delas, não deixa no deserto as noventa e nove, e vai em busca da perdida, até que a encontre?", 2.4),
 V("Lucas 15:5", "E encontrando-a, não a ponha sobre seus ombros, com alegria?", 2.4),
 V("Lucas 15:6", "E vindo para casa, não convoque aos amigos, e vizinhos, dizendo-lhes: Alegrai-vos comigo, porque já achei minha ovelha perdida?", 3.0)] + falas("""
Uma ovelha em cem. Para muita gente, seria uma perda aceitável. Mas não para esse Pastor.
Ele vai atrás. Até encontrar. E quando encontra, não briga, não humilha, não manda voltar sozinha. Ele coloca a ovelha nos ombros e carrega para casa.
E faz festa.
Se você já se sentiu longe, esquecido, ou achou que tinha se afastado demais, guarde essa imagem: os ombros do Pastor, e a alegria dele em trazer você de volta.
""", "Meditação · Lucas 15")))

SEC.append(("João 10", 'deserto_estrelas', ['estrelas'],
 falas("""
E então Jesus disse, com todas as letras, quem é esse Pastor.
""", "João 10") + [V("João 10:11", "Eu sou o bom Pastor; o bom Pastor dá sua vida pelas ovelhas.", 2.4),
 V("João 10:14", "Eu sou o bom Pastor, e conheço as minhas, e pelas minhas sou conhecido.", 2.4),
 V("João 10:27", "Minhas ovelhas ouvem minha voz, e eu as conheço, e elas me seguem.", 2.4),
 V("João 10:28", "E eu lhes dou a vida eterna, e para sempre não perecerão, e ninguém as arrancará de minha mão.", 3.0)] + falas("""
O Pastor do Salmo vinte e três tem nome e rosto. Ele caminhou entre nós.
E Ele vai além de tudo o que Davi imaginou. Davi arriscou a vida diante de um leão. Jesus entregou a própria vida pelas ovelhas.
"Eu conheço as minhas." Ele conhece você. Seu nome, sua história, aquilo que você nunca contou a ninguém.
E ninguém pode arrancar você da mão dele. Nem o medo, nem o passado, nem a noite mais escura.
Você pode adormecer seguro nessa mão.
""", "Meditação · João 10")))

SEC.append(("Apocalipse 7", 'aguas_quietas', ['poeira'],
 falas("""
O último livro da Bíblia termina essa história de um jeito surpreendente. O Pastor aparece como Cordeiro. Aquele que se entregou pelas ovelhas agora conduz o rebanho para sempre.
""", "Apocalipse 7") + [V("Apocalipse 7:17", "Porque o Cordeiro, que está no meio do trono, os apascentará, e os guiará até fontes vivas de águas; e Deus limpará toda lágrima dos seus olhos.", 3.0)] + falas("""
As águas quietas do Salmo vinte e três se tornam fontes vivas. O descanso de uma noite se torna descanso eterno.
E há um detalhe de enorme ternura: Deus limpará toda lágrima. Não apenas acabará com o sofrimento. Ele mesmo, com as próprias mãos, enxugará as lágrimas do rosto de cada um.
Todas as lágrimas que você já chorou, inclusive as que ninguém viu, são conhecidas por Ele. Um dia, nenhuma delas vai ficar sem consolo.
""", "Meditação · Apocalipse 7:17")))

SEC.append(("Salmo 121", 'cedros_montanha', ['nevoa'],
 falas("""
Antes da oração, vamos ouvir mais um salmo. O Salmo cento e vinte e um era cantado pelos peregrinos que subiam a Jerusalém. É um salmo perfeito para a hora de dormir.
""", "Salmo 121") + [V(f"Salmo 121:{i+1}", t, 2.4) for i, t in enumerate([
 "Levanto meus olhos aos montes. De onde virá meu socorro?",
 "Meu socorro vem do SENHOR, que fez os céus e a terra.",
 "Ele não deixará o teu pé se abalar, nem cochilará o teu guardião.",
 "Eis que não cochilará nem dormirá o Guardião de Israel.",
 "O SENHOR é o teu guardião; o SENHOR é a sombra à tua direita.",
 "O sol não te ferirá durante o dia, nem a lua durante a noite.",
 "O SENHOR te guardará de todo mal; ele guardará a tua alma.",
 "O SENHOR guardará tua saída e tua entrada, desde agora e para sempre."])] + falas("""
Os peregrinos olhavam para os montes no caminho e sabiam dos perigos que havia ali. Ladrões, animais, o calor do dia, o frio da noite.
E a pergunta era sincera: de onde vem o meu socorro? A resposta vem logo: do Senhor, que fez os céus e a terra.
Agora repare em uma frase: Ele não cochila, nem dorme.
É por isso que você pode dormir. Você não precisa ficar de vigia. Não precisa segurar o mundo com as próprias mãos durante a noite. Existe um Guardião acordado.
Pode fechar os olhos. Ele continua olhando por você.
""", "Meditação · Salmo 121")))

SEC.append(("Gratidão pelo dia", 'lamparina_mesa', ['poeira'], falas("""
Antes de orar, vamos fazer algo simples. Vamos olhar para o dia de hoje com gratidão.
Respire devagar. E pense em um momento bom que aconteceu hoje. Pode ser pequeno. Um café quente, uma conversa, uma mensagem de alguém, um minuto de silêncio.
Agradeça por ele em silêncio.
Agora pense em uma pessoa que cruzou o seu caminho hoje. Alguém da família, do trabalho, ou até um desconhecido. Entregue essa pessoa ao cuidado do Pastor.
E se houve algo difícil hoje, uma palavra dura, um erro, uma frustração, não precisa carregar isso para dentro do sono. Coloque nas mãos de Deus.
O dia de hoje terminou. O que foi feito, foi feito. O que ficou para trás, Ele sabe cuidar.
Amanhã é um novo dia. As misericórdias dEle se renovam a cada manhã.
""", "Gratidão")))

SEC.append(("Oração da noite", 'casa_noite', ['estrelas'], falas("""
Vamos orar.
Senhor, meu Pastor, obrigado por mais este dia.
Obrigado porque, mesmo quando eu não percebi, Tu estavas cuidando de mim.
Eu entrego em Tuas mãos tudo o que ficou por fazer. As tarefas, as conversas, as decisões que ainda não sei como tomar.
Entrego também as pessoas que eu amo. Cuida delas onde estiverem esta noite.
Se há alguma tristeza no meu coração, Senhor, restaura a minha alma. Se há culpa, me lembra do Teu perdão. Se há medo, me lembra de que Tu estás comigo.
Faz-me deitar em pastos verdes. Leva-me para perto de águas quietas. Acalma os meus pensamentos.
Que eu durma em paz, sabendo que estou na Tua mão, e que ninguém pode me arrancar dela.
E que amanhã eu acorde com a certeza de que a Tua bondade e a Tua misericórdia vão me acompanhar.
Em nome de Jesus, o bom Pastor. Amém.
""", "Oração da noite")))

SEC.append(("Leitura final e bênção", 'lago_nevoa', ['nevoa'],
 falas("""
Para terminar, vamos ouvir mais uma vez o Salmo vinte e três. Bem devagar. Deixe cada frase pousar.
""", "Leitura final") + [V(f"Salmo 23:{i+1}", t, 4.0) for i, t in enumerate(S23)] + falas("""
E receba agora a bênção que Deus mandou pronunciar sobre o seu povo:
""", "Bênção") + [V("Números 6:24", "O SENHOR te abençoe, e te guarde:", 2.0),
 V("Números 6:25", "Faça resplandecer o SENHOR seu rosto sobre ti, e tenha de ti misericórdia:", 2.0),
 V("Números 6:26", "O SENHOR levante a ti seu rosto, e ponha em ti paz.", 4.0)] + falas("""
Boa noite. Descanse em paz. O Pastor está cuidando de você.
""", "Boa noite")))

blocos = [{'cenario': c, 'efeito': e, 'itens': it} for _, c, e, it in SEC]
for b in blocos: b['itens'][-1]['pausa'] = max(b['itens'][-1].get('pausa', 2), 4.0)
R = {'titulo': 'Salmo 23', 'subtitulo': 'O Senhor é o meu pastor', 'voz': 'pm_santa', 'velocidade': 1.0,
     'pausa_verso': 2.4, 'ambiente': 'riacho', 'fps': 24, 'cauda': 20, 'fim': 'Dádiva dos Céus', 'blocos': blocos}
json.dump(R, open(f'{AQUI}/salmo-23-completo.json', 'w'), ensure_ascii=False, indent=1)
md = ["# Salmo 23 — O Senhor é o meu pastor (narração contínua, ~28 min)\n",
      "Textos bíblicos: Bíblia Livre (BLIVRE), CC BY 4.0. Meditações e oração: texto original do canal.\n"]
for n, (tit, cen, _, its) in enumerate(SEC, 1):
    md.append(f"\n## {n}. {tit}\n")
    for it in its:
        md.append(f"> **{it['ref']}** — {it['texto']}\n" if it['tipo'] == 'verso' else it['texto'] + "\n")
open(f'{AQUI}/salmo-23-completo-roteiro.md', 'w').write('\n'.join(md))
print('palavras', sum(len(it['texto'].split()) for _, _, _, its in SEC for it in its))
