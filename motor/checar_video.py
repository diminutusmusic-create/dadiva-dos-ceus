"""Checagem obrigatória antes de qualquer envio. Uso: python motor/checar_video.py <video.mp4> [dur_min] [dur_max]
Falha (exit 1) se: sem faixa de áudio; trecho mudo > 3 s; trecho preto > 1.5 s fora do início/fim; duração fora do intervalo."""
import sys, subprocess, re, json
v = sys.argv[1]; dmin = float(sys.argv[2]) if len(sys.argv) > 2 else 0; dmax = float(sys.argv[3]) if len(sys.argv) > 3 else 1e9
pr = json.loads(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration:stream=codec_type', '-of', 'json', v], capture_output=True, text=True).stdout)
dur = float(pr['format']['duration']); tipos = [s['codec_type'] for s in pr['streams']]
erros = []
if 'audio' not in tipos: erros.append('sem faixa de áudio')
if not dmin <= dur <= dmax: erros.append(f'duração {dur:.1f}s fora de [{dmin}, {dmax}]')
log = subprocess.run(['ffmpeg', '-nostdin', '-hide_banner', '-i', v, '-af', 'silencedetect=n=-45dB:d=3', '-vf', 'blackdetect=d=1.5:pix_th=0.06',
                      '-f', 'null', '-'], capture_output=True, text=True).stderr
for a, b in re.findall(r'silence_start: ([\d.]+)[\s\S]*?silence_end: ([\d.]+)', log):
    erros.append(f'áudio mudo {float(a):.1f}s → {float(b):.1f}s ({float(b) - float(a):.1f}s)')
if re.search(r'silence_start: [\d.]+(?![\s\S]*silence_end)', log): erros.append('áudio mudo até o fim')
for a, b in re.findall(r'black_start:([\d.]+) black_end:([\d.]+)', log):
    if float(a) > 1 and float(b) < dur - 6: erros.append(f'tela preta {float(a):.1f}s → {float(b):.1f}s')
print(('OK ' if not erros else 'FALHOU ') + f'{v} ({dur:.0f}s)')
for e in erros[:20]: print('  -', e)
if len(erros) > 20: print(f'  ... +{len(erros) - 20}')
sys.exit(1 if erros else 0)
