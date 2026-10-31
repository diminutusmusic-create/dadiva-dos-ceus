# Treina uma voz RVC (Applio) com a cantora de "O Meu Refúgio" e converte a voz de "Em Paz Me Deito".
# Rodar no Kaggle (GPU): exec(urllib.request.urlopen(RAW).read().decode())
import os, subprocess, sys, glob, shutil, urllib.request, time
W = '/kaggle/working'; A = f'{W}/Applio'; os.chdir(W)
os.environ['APPLIO_LOGS_DIR'] = f'{W}/logs'
def sh(cmd, cwd=A):
    print('>>', cmd[:160], flush=True)
    p = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
    out = (p.stdout or '') + (p.stderr or '')
    print(out[-2500:], flush=True)
    if p.returncode: raise SystemExit(f'FALHOU ({p.returncode}): {cmd[:80]}')
    return out
if not os.path.exists(A):
    sh('git clone -q --depth 1 https://github.com/IAHispano/Applio.git', cwd=W)
    sh('pip install -q faiss-cpu librosa soundfile stftpitchshift soxr torchcrepe torchfcpe einops "transformers>=4.45" '
       'tensorboard onnx onnxruntime webrtcvad-wheels edge-tts beautifulsoup4 psutil noisereduce pedalboard')
sys.path.insert(0, A); os.chdir(A)
import core
print(core.run_prerequisites_script(pretraineds_hifigan=True, models=True, exe=False), flush=True)
U = 'https://raw.githubusercontent.com/diminutusmusic-create/dadiva-dos-ceus/uploads/rvc/'
DS = f'{W}/dataset'; os.makedirs(DS, exist_ok=True)
for n in ['refugio_vocals.flac', 'empaz_vocals.flac']:
    if not os.path.exists(f'{W}/{n}'): urllib.request.urlretrieve(U + n, f'{W}/{n}')
# dataset: só a voz de O Meu Refúgio, em mono 48k
sh(f'ffmpeg -y -loglevel error -i {W}/refugio_vocals.flac -ac 1 -ar 48000 {DS}/refugio.wav', cwd=W)
M, SR, PY = 'cantora_dadiva', 48000, sys.executable
LOG = f'{W}/logs/{M}'
if not glob.glob(f'{LOG}/{M}_*e_*s.pth'):
    sh(f'{PY} rvc/train/preprocess/preprocess.py {LOG} {DS} {SR} 4 Automatic False 3.0 0.3 none')
    sh(f'{PY} rvc/train/extract/extract.py {LOG} rmvpe 4 0 {SR} contentvec None 2')
    pg, pd = core.pretrained_selector('HiFi-GAN', SR)
    t0 = time.time()
    sh(f'{PY} rvc/train/train.py {M} 100 300 {pg} {pd} 0 8 {SR} True True False False HiFi-GAN False')
    print('treino em', round((time.time() - t0) / 60, 1), 'min', flush=True)
    sh(f'{PY} rvc/train/process/extract_index.py {LOG} Auto')
pth = sorted(glob.glob(f'{LOG}/{M}_*e_*s.pth'), key=os.path.getmtime)[-1]
idx = (glob.glob(f'{LOG}/*.index') or [''])[0]
print('modelo', pth, 'index', idx, flush=True)
OUT = f'{W}/saida_rvc'; os.makedirs(OUT, exist_ok=True)
for ir, prot in [(0.5, 0.33), (0.75, 0.4)]:
    o = f'{OUT}/empaz_convertida_ir{int(ir*100)}.wav'
    print(core.run_infer_script(pitch=0, index_rate=ir, volume_envelope=1.0, protect=prot, f0_method='rmvpe',
          input_path=f'{W}/empaz_vocals.flac', output_path=o, pth_path=pth, index_path=idx,
          f0_autotune=False, f0_autotune_strength=1.0, proposed_pitch=False, proposed_pitch_threshold=155.0,
          export_format='WAV', embedder_model='contentvec'), flush=True)
shutil.copy(pth, f'{OUT}/{M}.pth')
if idx: shutil.copy(idx, f'{OUT}/{M}.index')
os.chdir(W); shutil.make_archive('rvc_teste', 'zip', OUT)
print('PRONTO', os.listdir(OUT), round(os.path.getsize(f'{W}/rvc_teste.zip') / 1e6, 1), 'MB')
