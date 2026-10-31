"""Offline any->English translation (Argos Translate, auto-installs language packs)."""
import threading
from langdetect import detect, DetectorFactory
import argostranslate.package as pkg
import argostranslate.translate as tr

DetectorFactory.seed = 0
_lock = threading.Lock()
_index_ready = False
_cache: dict = {}


def _has_pair(src):
    langs = {l.code: l for l in tr.get_installed_languages()}
    if src not in langs or "en" not in langs:
        return False
    return langs[src].get_translation(langs["en"]) is not None


def _install(src):
    global _index_ready
    if _has_pair(src):
        return
    if not _index_ready:
        pkg.update_package_index()
        _index_ready = True
    for p in pkg.get_available_packages():
        if p.from_code == src and p.to_code == "en":
            pkg.install_from_path(p.download())
            return
    raise RuntimeError("No language pack %s->en available" % src)


def to_english(text, src=None):
    text = text.strip()
    if not text:
        return ""
    if text in _cache:
        return _cache[text]
    try:
        src = src or detect(text)
    except Exception:
        return text
    if src == "en":
        return text
    if src.startswith("zh"):
        src = "zh"
    with _lock:
        try:
            _install(src)
            out = tr.translate(text, src, "en")
        except Exception as ex:
            out = "[%s]" % ex if not _cache else text
    _cache[text] = out
    return out
