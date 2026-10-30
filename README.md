# Dádiva dos Céus

Gerador automático das histórias bíblicas animadas do canal **Dádiva dos Céus**.

roteiro (JSON) → narração (Kokoro, grátis) → animação dos personagens → legendas → trilha → MP4 vertical 1080x1920

## Pastas
- `roteiros/` — um arquivo JSON por episódio (falas, personagens, cenário, descrição e hashtags)
- `arte/` — personagens e cenários (gerados com Z-Image-Turbo no Kaggle)
- `motor/` — o código (`episodio.py` gera um vídeo)
- `videos/` — vídeos prontos (links públicos usados pelo Metricool para agendar)
- `marca/` — foto de perfil, banner do YouTube e capa do Facebook
- `fontes/` — fontes Cinzel e Cormorant Garamond (licença OFL)

## Gerar um episódio
```
pip install skia-python kokoro-onnx soundfile scipy numpy pillow
mkdir modelos
curl -L -o modelos/kokoro-v1.0.onnx https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx
curl -L -o modelos/voices-v1.0.bin https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin
python motor/episodio.py roteiros/001-a-ovelha-perdida.json
```
Precisa do FFmpeg instalado. Vídeos devem passar de 61 s para valer no Programa de Recompensas do TikTok.
