import subprocess, sys
subprocess.run([sys.executable,'-m','pip','install','-q','-U','diffusers','transformers','accelerate'],check=True)
import os, gc, glob, torch, urllib.request, shutil
os.environ['PYTORCH_CUDA_ALLOC_CONF']='expandable_segments:True'
if 'pipe' not in globals():
    from diffusers import DiffusionPipeline
    pipe = DiffusionPipeline.from_pretrained('Tongyi-MAI/Z-Image-Turbo', torch_dtype=torch.bfloat16)
    pipe.enable_model_cpu_offload()
from PIL import Image
OUT = 'paisagens2'; os.makedirs(OUT, exist_ok=True)
F = ("cinematic landscape photograph, photorealistic, shot on full frame camera, 35mm lens, natural soft light, "
     "subtle film grain, calm and peaceful mood, muted warm color grading, high detail, wide horizontal composition, "
     "no people, no humans, no text, no watermark, ")
CEN = {
 'rocha_fortaleza': "a massive rocky cliff fortress in the Judean desert at golden hour, a small cave opening with warm light, ",
 'asas_aguia': "a lone eagle soaring with wide open wings above misty mountains at sunrise, ",
 'tenda_estrelas': "a simple ancient bedouin tent glowing softly at night in the desert under a sky full of stars, ",
 'monte_nuvens': "a high mountain peak above a sea of clouds at dawn, soft pink light, ",
 'monte_galileia': "a green grassy hill overlooking the Sea of Galilee in the early morning, wildflowers, gentle light, ",
 'flores_campo': "a meadow full of white and purple wild lilies swaying, soft late afternoon light, shallow depth of field, ",
 'oliveiras_pombas': "an olive grove at sunset with a few white doves resting on the branches, warm golden light, ",
 'juncos_amanhecer': "a quiet lake shore with reeds at dawn, mirror-like water, thin mist, ",
 'mar_amanhecer': "the sea horizon at dawn, first light spreading over calm water, wings of morning, ",
 'oceano_noite': "a calm ocean at night under the milky way, gentle waves reflecting starlight, ",
 'floresta_raios': "an ancient forest with tall trees and god rays of light through morning mist, ",
 'vale_nascer': "a wide valley at sunrise filled with soft mist, golden rays over the hills, ",
 'passaros_campo': "a flock of small birds flying over a golden field at sunset, ",
 'trigo_dourado': "a golden wheat field close up in warm evening light, gentle breeze, ",
 'jardim_manha': "a peaceful garden at early morning with dew on the leaves and soft light, ",
 'casa_luz': "an ancient stone house with many windows glowing with warm light at blue hour, ",
 'caminho_luz': "an old stone path through a field leading toward a bright warm sunrise, ",
 'rio_salgueiro': "a quiet river with a weeping willow tree at dusk, calm water reflections, ",
 'janela_chuva': "a rustic window at night with rain drops on the glass and a warm candle light inside, ",
 'luz_montanhas': "sunlight breaking through dark clouds over mountains, dramatic rays of light, ",
 'lamparina_pedra': "an oil lamp glowing in a dark ancient stone room, warm light on the walls, ",
 'rochas_alto': "a high rocky outcrop above a valley, safe and solid, at golden hour, ",
 'jerusalem_aurora': "the hills around ancient Jerusalem at dawn, soft fog in the valleys, ",
 'ceu_aurora': "a vast sky at dawn with soft clouds in pink and gold over a quiet landscape, ",
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
shutil.make_archive('paisagens2', 'zip', OUT)
fs = [f for f in sorted(glob.glob(f'{OUT}/*.png')) if not f.endswith('_depth.png')]
th = [Image.open(f).convert('RGB').resize((320, 180)) for f in fs]
sh = Image.new('RGB', (320 * 4, 180 * ((len(th) + 3) // 4)), 'black')
for i, t in enumerate(th): sh.paste(t, ((i % 4) * 320, (i // 4) * 180))
sh.save('contato_paisagens2.jpg', quality=85); print('PRONTO', len(fs)); display(sh)
