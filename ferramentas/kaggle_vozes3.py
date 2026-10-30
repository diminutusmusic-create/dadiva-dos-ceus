# Clonagem a partir de locutor brasileiro nativo (TTS-Portuguese Corpus, CC BY 4.0, feito para síntese de voz)
import subprocess, sys, os, glob, shutil, textwrap, re, json
os.chdir('/kaggle/working'); os.makedirs('vozes3', exist_ok=True)
def run(cmd):
    print('$', cmd[:150], flush=True); r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    print(r.stdout[-1200:], r.stderr[-2000:], flush=True)
if not glob.glob('corpus/**/*.wav', recursive=True):
    run('wget -q -O corpus.zip "https://www.dropbox.com/s/ohpc7epowv9ct7o/TTS-Portuguese-Corpus.zip?dl=1" && mkdir -p corpus && unzip -q corpus.zip -d corpus')
wavs = {os.path.basename(w): w for w in glob.glob('corpus/**/*.wav', recursive=True)}
print('wavs', len(wavs))
trans = {}
for f in glob.glob('corpus/**/*.csv', recursive=True) + glob.glob('corpus/**/*.txt', recursive=True):
    for ln in open(f, encoding='utf-8', errors='ignore'):
        m = re.match(r'\s*([^|=]+?\.wav)\s*(?:\||==)\s*(.+)', ln.strip())
        if m: trans[os.path.basename(m.group(1).strip())] = m.group(2).strip()
print('transcricoes', len(trans), list(trans.items())[:2])
import soundfile as sf, numpy as np
# junta 3-4 frases seguidas (~12-16 s) como referência
nomes = sorted(n for n in trans if n in wavs)
best = None
for i in range(200, len(nomes) - 4):
    grp = nomes[i:i + 4]; dur = sum(sf.info(wavs[n]).duration for n in grp)
    if 12 <= dur <= 16: best = grp; break
aud = []; sr0 = None
for n in best:
    a, sr0 = sf.read(wavs[n]); aud += [a, np.zeros(int(sr0 * .35))]
sf.write('vozes3/ref_br.wav', np.concatenate(aud), sr0)
REF_TXT = ' '.join(trans[n] for n in best)
TXT = ("O Senhor é meu pastor, nada me faltará. Ele me faz deitar em pastos verdes, e me leva a águas quietas. "
       "Ele restaura minha alma, e me guia pelos caminhos da justiça por seu nome.")
json.dump({'ref_txt': REF_TXT, 'txt': TXT}, open('vozes3/cfg.json', 'w'), ensure_ascii=False)
print('REF', REF_TXT, flush=True)
QWEN = textwrap.dedent('''
import json, torch, soundfile as sf
from qwen_tts import Qwen3TTSModel
c = json.load(open('vozes3/cfg.json'))
m = Qwen3TTSModel.from_pretrained("Qwen/Qwen3-TTS-12Hz-1.7B-Base", device_map="cuda:0", dtype=torch.float16, attn_implementation="sdpa")
for s in (7, 11):
    torch.manual_seed(s)
    w, sr = m.generate_voice_clone(text=c['txt'], language="Portuguese", ref_audio='vozes3/ref_br.wav', ref_text=c['ref_txt'])
    sf.write(f"vozes3/qwen_clone_{s}.wav", w[0], sr); print("ok qwen", s, flush=True)
''')
VOX = textwrap.dedent('''
import json, soundfile as sf
from voxcpm import VoxCPM
c = json.load(open('vozes3/cfg.json'))
m = VoxCPM.from_pretrained("openbmb/VoxCPM2", load_denoiser=False)
w = m.generate(text=c['txt'], prompt_wav_path='vozes3/ref_br.wav', prompt_text=c['ref_txt'], reference_wav_path='vozes3/ref_br.wav', cfg_value=2.0, inference_timesteps=10, seed=7)
sf.write("vozes3/voxcpm_clone.wav", w, m.tts_model.sample_rate); print("ok voxcpm 1", flush=True)
w = m.generate(text="(calm, slow, warm and reverent)" + c['txt'], reference_wav_path='vozes3/ref_br.wav', cfg_value=2.0, inference_timesteps=10, seed=7)
sf.write("vozes3/voxcpm_clone_calmo.wav", w, m.tts_model.sample_rate); print("ok voxcpm 2", flush=True)
''')
open('t3_qwen.py', 'w').write(QWEN); open('t3_vox.py', 'w').write(VOX)
run(f'{sys.executable} -m pip install -q -U qwen-tts')
run(f'{sys.executable} t3_qwen.py')
if not os.path.exists('vx/bin/python'):
    run(f'{sys.executable} -m pip install -q uv && uv venv vx --python 3.12 -q && uv pip install -q --python vx/bin/python voxcpm soundfile')
run('vx/bin/python t3_vox.py')
shutil.make_archive('vozes3', 'zip', 'vozes3'); print('PRONTO', sorted(glob.glob('vozes3/*.wav')))
