import subprocess, sys
subprocess.run([sys.executable,'-m','pip','install','-q','-U','diffusers','transformers','accelerate'],check=True)
import os, gc, glob, torch
os.environ['PYTORCH_CUDA_ALLOC_CONF']='expandable_segments:True'
if 'pipe' not in globals():
    from diffusers import DiffusionPipeline
    pipe = DiffusionPipeline.from_pretrained('Tongyi-MAI/Z-Image-Turbo', torch_dtype=torch.bfloat16)
    pipe.enable_model_cpu_offload()
from PIL import Image
E = ("flat vector cartoon illustration, clean bold dark brown outlines, cel shading with one shadow tone, "
     "soft warm colors, friendly children's bible storybook style, high quality, ")
P = ("full body character, front view, standing straight, arms slightly away from the body, "
     "feet visible, plain pure white background, centered, no text")
A = "full body, side view, plain pure white background, centered, no text"
O = "single object, plain pure white background, centered, no text"
C = "wide landscape background, no people, vertical composition, no text"
CHAR = {
 'noe': "Noah from the Bible, old man with long white beard, kind smile, brown and beige robe, wooden staff, sandals, ",
 'moises': "Moses from the Bible, middle aged man with long gray beard and brown hair, red and beige robe, holding a wooden staff, sandals, ",
 'jonas': "Jonah from the Bible, young man with short black beard, worried face, blue and beige tunic, sandals, ",
 'daniel': "Daniel from the Bible, young man with short brown hair, calm face, purple and gold robe, sandals, ",
 'pedro': "Peter the apostle, strong fisherman with short curly gray beard, green tunic, rope belt, sandals, ",
 'maria': "Mary mother of Jesus, young woman, gentle smile, blue head veil over white robe, sandals, ",
 'jose_carpinteiro': "Joseph the carpenter, young man with short brown beard, brown and green robe, sandals, ",
 'jose_egito': "Joseph son of Jacob, young man, cheerful, wearing a long coat of many bright colors with stripes, sandals, ",
 'zaqueu': "Zacchaeus, very short man, small round body, big nose, short black beard, rich orange and gold robe, ",
 'filho_prodigo': "young man in torn dirty brown clothes, sad face, barefoot, the prodigal son, ",
 'pai': "elderly father with white beard, joyful face, open arms, long beige and blue robe, sandals, ",
 'samaritano': "good samaritan, middle aged man with black beard and turban, green and red striped robe, sandals, ",
 'ferido': "wounded traveler sitting on the ground, bandaged head and arm, simple white tunic, ",
 'menino_paes': "little boy holding a basket with five loaves of bread and two fish, short tunic, big smile, ",
 'rute': "Ruth from the Bible, young woman, warm smile, head scarf, beige and red dress, holding wheat sheaves, ",
}
ANIM = {
 'ovelha': "a cute white fluffy sheep, ", 'leao': "a big friendly lion with golden mane, sitting, ",
 'peixe': "a giant friendly blue whale fish, smiling, ", 'burro': "a small gray donkey with a saddle, ",
 'pomba': "a white dove flying with an olive branch in its beak, ",
}
OBJ = {'arca': "Noah's ark, big wooden boat with a house on top, ", 'barco': "small wooden fishing boat with one sail, "}
CEN = {
 'diluvio': "great flood, heavy rain, dark stormy sea, Noah's ark floating far away, ",
 'arco_iris': "calm green mountains after the rain, big bright rainbow, Noah's ark resting on a mountain, ",
 'mar_tempestade': "stormy sea with big waves, lightning, dark clouds, ",
 'mar_noite': "calm sea at night, full moon, stars, soft reflections, ",
 'cova_leoes': "inside a stone lions den, rocky cave walls, light coming from an opening above, ",
 'mar_vermelho': "the Red Sea parted into two tall walls of water, dry path in the middle, sunset sky, ",
 'estrada_deserto': "rocky desert road between hills, a few bushes, hot afternoon sun, ",
 'fazenda': "simple farm with a stone house, fields, pig pen, olive trees, warm light, ",
 'jerico': "ancient city street of Jericho with a big sycamore tree, stone houses, palm trees, ",
 'colina_multidao': "green hillside by a lake, large crowd of tiny people sitting on the grass far away, ",
 'estabulo': "humble wooden stable at night, manger with hay, a bright star in the sky, ",
 'egito': "ancient Egypt, pyramids, palm trees by the Nile river, golden light, ",
 'campo_trigo': "golden wheat field at sunset, small village far away, ",
 'nascer_sol': "peaceful field at sunrise, soft rays of light, flowers, ",
 'ceu_estrelado': "starry night sky over desert hills, milky way, ",
}
os.makedirs('lote2', exist_ok=True)
def gerar(nome, prompt, sizes, seed):
    if os.path.exists(f'lote2/{nome}_{seed}.png'): return
    for (w, h) in sizes:
        ok = False
        try:
            g = torch.Generator('cpu').manual_seed(seed)
            img = pipe(prompt=prompt, width=w, height=h, num_inference_steps=9, guidance_scale=0.0, generator=g).images[0]
            img.save(f'lote2/{nome}_{seed}.png'); print('ok', nome, seed, flush=True); ok = True
        except torch.cuda.OutOfMemoryError:
            print('memoria', nome, flush=True)
        gc.collect(); torch.cuda.empty_cache()
        if ok: return
PS = [(640, 864), (576, 768)]; SQ = [(768, 768), (640, 640)]; CS = [(544, 960), (480, 848)]
for n, p in CHAR.items():
    for s in (100, 101): gerar(n, E + p + P, PS, s)
for n, p in ANIM.items(): gerar(n, E + p + A, SQ, 100)
for n, p in OBJ.items(): gerar(n, E + p + O, SQ, 100)
for n, p in CEN.items(): gerar(n, E + p + C, CS, 200)
import shutil; shutil.make_archive('lote2', 'zip', 'lote2')
fs = sorted(glob.glob('lote2/*.png')); th = [Image.open(f).convert('RGB') for f in fs]
th = [t.resize((200, int(200 * t.height / t.width))) for t in th]
cols = 8; hm = max(t.height for t in th); rows = (len(th) + cols - 1) // cols
sh = Image.new('RGB', (200 * cols, hm * rows), 'white')
for i, t in enumerate(th): sh.paste(t, ((i % cols) * 200, (i // cols) * hm))
sh.save('contato2.jpg', quality=80); print('PRONTO', len(fs)); display(sh)
