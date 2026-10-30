# Dia 1.6B fine-tuned para português do Brasil (Alissonerdx/Dia1.6-pt_BR-v1, Apache 2.0)
import subprocess, sys, os, glob, shutil, textwrap
os.chdir('/kaggle/working'); os.makedirs('vozes4', exist_ok=True)
def run(cmd):
    print('$', cmd[:150], flush=True); r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    print(r.stdout[-1500:], r.stderr[-2500:], flush=True)
DIA = textwrap.dedent('''
import torch, soundfile as sf, numpy as np
from huggingface_hub import hf_hub_download
from dia.model import Dia
rep = "Alissonerdx/Dia1.6-pt_BR-v1"
cfg = hf_hub_download(rep, "config.json")
for nome in ["Dia1.6-Portuguese-v1.safetensors", "Dia1.6-Portuguese-v1.pth"]:
    try: ck = hf_hub_download(rep, nome); break
    except Exception as e: print("sem", nome, e)
m = Dia.from_local(cfg, ck, compute_dtype="float16", device=torch.device("cuda"))
FR = ["[S1] O Senhor é meu pastor, nada me faltará. Ele me faz deitar em pastos verdes, e me leva a águas quietas.",
      "[S1] Ele restaura minha alma, e me guia pelos caminhos da justiça por seu nome."]
for s in (1, 2, 3):
    torch.manual_seed(s); np.random.seed(s)
    partes = []
    for t in FR:
        a = m.generate(t, use_torch_compile=False, verbose=False, cfg_scale=3.0, temperature=1.2, top_p=0.95)
        partes += [np.asarray(a, np.float32), np.zeros(int(44100 * .9), np.float32)]
    sf.write(f"vozes4/dia_ptbr_{s}.wav", np.concatenate(partes), 44100); print("ok dia", s, flush=True)
''')
open('t4_dia.py', 'w').write(DIA)
if not os.path.exists('dvx/bin/python'):
    run(f'{sys.executable} -m pip install -q uv && uv venv dvx --python 3.12 -q && uv pip install -q --python dvx/bin/python "git+https://github.com/nari-labs/dia.git" soundfile huggingface_hub')
run('dvx/bin/python t4_dia.py')
shutil.make_archive('vozes4', 'zip', 'vozes4'); print('PRONTO', sorted(glob.glob('vozes4/*.wav')))
