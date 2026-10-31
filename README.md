# On-Screen Translator
Windows 11 app: translate any on-screen language to English - live screen regions, images, video files, and text. Offline after first language-pack download (OCR: RapidOCR; translation: Argos Translate).

## Run
`pip install -r requirements.txt` then `python run.py`

## Build .exe
Run `build_exe.bat` (output `dist/OnScreenTranslator/OnScreenTranslator.exe`) or download the artifact from the GitHub Actions "build-exe" workflow.

## Notes
- Video files: OCR every 15th frame; output is an .mp4 without audio.
- Streaming video (YouTube etc.): use "Select screen region" while it plays.
