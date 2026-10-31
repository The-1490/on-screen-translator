"""OCR with RapidOCR (ONNX, CPU, multilingual)."""
import numpy as np
from PIL import Image

_engine = None


def _get():
    global _engine
    if _engine is None:
        from rapidocr_onnxruntime import RapidOCR
        _engine = RapidOCR()
    return _engine


def read(img):
    """Return [((x,y,w,h), text)] for a PIL image or ndarray."""
    arr = np.array(img.convert("RGB")) if isinstance(img, Image.Image) else img
    result, _ = _get()(arr)
    out = []
    for box, text, conf in result or []:
        if float(conf) < 0.5 or not text.strip():
            continue
        xs = [p[0] for p in box]
        ys = [p[1] for p in box]
        x, y = int(min(xs)), int(min(ys))
        out.append(((x, y, int(max(xs)) - x, int(max(ys)) - y), text))
    return out
