import subprocess, sys, os, glob, shutil, urllib.request
os.chdir('/kaggle/working')
if not os.path.exists('cbx'):
    subprocess.run(['git', 'clone', '-q', 'https://huggingface.co/spaces/ResembleAI/Chatterbox-Multilingual-TTS-pt-br', 'cbx'], check=True)
    subprocess.run([sys.executable, '-m', 'pip', 'install', '-q', 's3tokenizer', 'resemble-perth==1.0.1', 'silero-vad==5.1.2',
                    'conformer==0.3.2', 'omegaconf==2.3.0', 'librosa', 'resampy', 'safetensors', 'transformers==4.46.3',
                    'diffusers==0.29.0'], check=False)
sys.path.insert(0, '/kaggle/working/cbx')
import torch, numpy as np, soundfile as sf
from chatterbox.src.chatterbox.tts import ChatterboxTTS
if 'MODEL' not in globals():
    MODEL = ChatterboxTTS.from_pretrained('cuda')
os.makedirs('vozes/ref', exist_ok=True)
BASE = 'https://storage.googleapis.com/chatterbox-demo-samples/mtl-v3-single-language-prompts/pt-br/'
refs = []
for n in ['pt_br_m1', 'pt_br_m2', 'pt_br_m3', 'pt_br_m4', 'pt_br_f1', 'pt_br_f2', 'pt_br_f3']:
    try:
        urllib.request.urlretrieve(BASE + n + '.wav', f'vozes/ref/{n}.wav'); refs.append(n); print('ref', n)
    except Exception as e: print('sem', n)
TXT = ("O Senhor é meu pastor, nada me faltará. Ele me faz deitar em pastos verdes, e me leva a águas quietas. "
       "Ele restaura minha alma, e me guia pelos caminhos da justiça por seu nome.")
AJ = [('calma', .3, .4, .7), ('padrao', .5, .5, .8)]
for r in refs:
    for nome, ex, cfg, tp in AJ:
        torch.manual_seed(7)
        w = MODEL.generate(TXT, language_id='pt', audio_prompt_path=f'vozes/ref/{r}.wav', exaggeration=ex, cfg_weight=cfg, temperature=tp)
        sf.write(f'vozes/{r}_{nome}.wav', w.squeeze(0).cpu().numpy(), MODEL.sr); print('ok', r, nome, flush=True)
torch.manual_seed(7)
w = MODEL.generate(TXT, language_id='pt', exaggeration=.3, cfg_weight=.4, temperature=.7)
sf.write('vozes/padrao_modelo_calma.wav', w.squeeze(0).cpu().numpy(), MODEL.sr)
shutil.make_archive('vozes', 'zip', 'vozes'); print('PRONTO', len(glob.glob('vozes/*.wav')))
