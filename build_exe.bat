@echo off
python -m venv .venv && call .venv\Scripts\activate
pip install -r requirements.txt
pyinstaller --noconfirm --onedir --windowed --name OnScreenTranslator --paths src ^
 --collect-all rapidocr_onnxruntime --collect-all argostranslate --collect-all stanza --collect-all ctranslate2 --collect-all sentencepiece run.py
echo Output: dist\OnScreenTranslator\OnScreenTranslator.exe
