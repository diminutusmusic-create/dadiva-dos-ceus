import subprocess, sys, os, glob, shutil, textwrap
os.chdir('/kaggle/working'); os.makedirs('vozes2', exist_ok=True)
TXT = ("O Senhor é meu pastor, nada me faltará. Ele me faz deitar em pastos verdes, e me leva a águas quietas. "
       "Ele restaura minha alma, e me guia pelos caminhos da justiça por seu nome.")
VOZES = {
 'masc_grave': "Brazilian Portuguese male narrator, about 50 years old, deep warm baritone, calm, slow and reverent, "
               "like a pastor softly reading the Bible at night, natural breathing, native Brazilian accent.",
 'masc_suave': "Brazilian Portuguese male voice, about 35 years old, soft warm tenor, intimate and peaceful, "
               "speaking slowly like a gentle bedtime prayer, native Brazilian accent from São Paulo.",
 'fem_suave':  "Brazilian Portuguese female voice, about 40 years old, warm and soothing, calm and slow, "
               "tender and reverent, softly reading psalms, native Brazilian accent.",
}
import json; json.dump({'txt': TXT, 'vozes': VOZES}, open('vozes2/cfg.json', 'w'))

QWEN = textwrap.dedent('''
import json, torch, soundfile as sf
from qwen_tts import Qwen3TTSModel
c = json.load(open('vozes2/cfg.json'))
m = Qwen3TTSModel.from_pretrained("Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign", device_map="cuda:0", dtype=torch.float16, attn_implementation="sdpa")
for k, d in c['vozes'].items():
    torch.manual_seed(7)
    w, sr = m.generate_voice_design(text=c['txt'], language="Portuguese", instruct=d)
    sf.write(f"vozes2/qwen_{k}.wav", w[0], sr); print("ok qwen", k, flush=True)
''')
VOX = textwrap.dedent('''
import json, soundfile as sf
from voxcpm import VoxCPM
c = json.load(open('vozes2/cfg.json'))
m = VoxCPM.from_pretrained("openbmb/VoxCPM2", load_denoiser=False)
for k, d in c['vozes'].items():
    w = m.generate(text="(" + d + ")" + c['txt'], cfg_value=2.0, inference_timesteps=10, seed=7)
    sf.write(f"vozes2/voxcpm_{k}.wav", w, m.tts_model.sample_rate); print("ok voxcpm", k, flush=True)
''')
open('t_qwen.py', 'w').write(QWEN); open('t_vox.py', 'w').write(VOX)
def run(cmd): print('$', cmd, flush=True); r = subprocess.run(cmd, shell=True, capture_output=True, text=True); print(r.stdout[-1500:], r.stderr[-2500:], flush=True)
run(f'{sys.executable} -m pip install -q -U qwen-tts')
run(f'{sys.executable} t_qwen.py')
run(f'{sys.executable} -m pip install -q -U voxcpm')
run(f'{sys.executable} t_vox.py')
shutil.make_archive('vozes2', 'zip', 'vozes2'); print('PRONTO', sorted(glob.glob('vozes2/*.wav')))
