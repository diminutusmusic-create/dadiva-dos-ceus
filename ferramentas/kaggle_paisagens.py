import subprocess, sys
subprocess.run([sys.executable,'-m','pip','install','-q','-U','diffusers','transformers','accelerate'],check=True)
import os, gc, glob, torch, urllib.request, shutil
os.environ['PYTORCH_CUDA_ALLOC_CONF']='expandable_segments:True'
if 'pipe' not in globals():
    from diffusers import DiffusionPipeline
    pipe = DiffusionPipeline.from_pretrained('Tongyi-MAI/Z-Image-Turbo', torch_dtype=torch.bfloat16)
    pipe.enable_model_cpu_offload()
from PIL import Image
OUT = 'paisagens'; os.makedirs(OUT, exist_ok=True)
F = ("cinematic landscape photograph, photorealistic, shot on full frame camera, 35mm lens, natural soft light, "
     "subtle film grain, calm and peaceful mood, muted warm color grading, high detail, wide horizontal composition, "
     "no people, no humans, no text, no watermark, ")
CEN = {
 'pastos_amanhecer': "rolling green hills in ancient Israel at dawn, soft golden mist in the valleys, a small flock of sheep grazing far away, ",
 'aguas_quietas': "a calm clear stream flowing slowly through green grass and smooth stones, reflections of a soft sky, gentle morning light, ",
 'caminho_oliveiras': "an old dirt path winding between ancient olive trees, soft sunbeams through the leaves, warm afternoon light, ",
 'vale_sombra': "a deep rocky valley in the Judean desert at dusk, long shadows, a single beam of warm light breaking through the clouds, ",
 'lamparina_mesa': "an ancient clay oil lamp glowing on a rustic wooden table at night, a simple clay cup, warm candle light, dark background, ",
 'casa_noite': "a small ancient stone house on a hill at night with warm light in the window, starry sky, milky way, ",
 'galileia_amanhecer': "the Sea of Galilee at sunrise, still water, soft pink and gold sky, distant hills, a small wooden boat on the shore, ",
 'deserto_estrelas': "Judean desert hills under a starry night sky, milky way, deep blue tones, ",
 'trigo_chuva': "golden wheat field under light rain at dusk, dark soft clouds, distant village lights, ",
 'jerusalem_entardecer': "ancient stone city on the hills of Jerusalem at sunset, cypress trees, warm golden haze, ",
 'lago_nevoa': "a quiet lake at blue hour with low fog over the water, pine and olive trees on the shore, ",
 'cedros_montanha': "majestic cedar trees on a mountain slope above the clouds at sunrise, soft light rays, ",
}
SIZES = [(1024, 576), (896, 512)]
def gerar(nome, prompt, seed=300):
    fn = f'{OUT}/{nome}.png'
    if os.path.exists(fn): return
    for (w, h) in SIZES:
        ok = False
        try:
            g = torch.Generator('cpu').manual_seed(seed)
            img = pipe(prompt=prompt, width=w, height=h, num_inference_steps=9, guidance_scale=0.0, generator=g).images[0]
            img.save(fn); print('ok', nome, w, h, flush=True); ok = True
        except torch.cuda.OutOfMemoryError:
            print('memoria', nome, w, flush=True)
        gc.collect(); torch.cuda.empty_cache()
        if ok: return
for n, p in CEN.items(): gerar(n, F + p)
# mapas de profundidade
from transformers import pipeline as hfpipe
dev = 1 if torch.cuda.device_count() > 1 else 0
dp = hfpipe('depth-estimation', model='depth-anything/Depth-Anything-V2-Base-hf', device=dev)
for fn in sorted(glob.glob(f'{OUT}/*.png')):
    if fn.endswith('_depth.png'): continue
    dfn = fn.replace('.png', '_depth.png')
    if os.path.exists(dfn): continue
    im = Image.open(fn).convert('RGB')
    d = dp(im)['depth'].resize(im.size, Image.BICUBIC)
    d.save(dfn); print('depth', fn, flush=True)
# texto da Biblia Livre (CC BY 4.0)
try:
    urllib.request.urlretrieve('https://ebible.org/Scriptures/porbr2018_usfm.zip', f'{OUT}/porbr2018_usfm.zip'); print('biblia ok')
except Exception as e: print('biblia falhou', e)
shutil.make_archive('paisagens', 'zip', OUT)
fs = [f for f in sorted(glob.glob(f'{OUT}/*.png')) if not f.endswith('_depth.png')]
th = [Image.open(f).convert('RGB').resize((320, 180)) for f in fs]
sh = Image.new('RGB', (320 * 4, 180 * ((len(th) + 3) // 4)), 'black')
for i, t in enumerate(th): sh.paste(t, ((i % 4) * 320, (i // 4) * 180))
sh.save('contato_paisagens.jpg', quality=85); print('PRONTO', len(fs)); display(sh)
