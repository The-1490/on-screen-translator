import cv2
import numpy as np
from PIL import Image
from . import ocr, translate, render


def translate_image(img):
    """Returns (annotated image, [(original, english)])."""
    items, pairs = [], []
    for box, text in ocr.read(img):
        en = translate.to_english(text)
        items.append((box, en))
        pairs.append((text, en))
    return render.overlay(img, items), pairs


def translate_video(src, dst, every_n=15, progress=None):
    """OCR every N frames, reuse the overlay in between. Output has no audio."""
    cap = cv2.VideoCapture(src)
    if not cap.isOpened():
        raise IOError("Cannot open %s" % src)
    fps = cap.get(cv2.CAP_PROP_FPS) or 25
    w, h = int(cap.get(3)), int(cap.get(4))
    vw = cv2.VideoWriter(dst, cv2.VideoWriter_fourcc(*"mp4v"), fps, (w, h))
    i, items = 0, []
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        pil = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        if i % every_n == 0:
            items = [(b, translate.to_english(t)) for b, t in ocr.read(pil)]
            if progress:
                progress(i)
        out = render.overlay(pil, items)
        vw.write(cv2.cvtColor(np.array(out), cv2.COLOR_RGB2BGR))
        i += 1
    cap.release()
    vw.release()
    return i
