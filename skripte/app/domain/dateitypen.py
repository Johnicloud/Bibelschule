"""Domäne: welche Art Datei ist das (nach der Endung)? Davon hängt ab, wie sie angezeigt und gelesen wird."""

ENDUNGEN = {
    "pdf": "pdf",
    "docx": "docx", "pages": "pages",
    "doc": "doc",                                                   # altes Word: nur herunterladen
    "txt": "text", "md": "text", "markdown": "text",
    "odt": "ansichtstext", "odp": "ansichtstext", "pptx": "ansichtstext",   # Text wird ausgelesen, kein Layout
    "png": "bild", "jpg": "bild", "jpeg": "bild", "webp": "bild", "gif": "bild",
    "mp3": "audio", "m4a": "audio", "aac": "audio", "wav": "audio", "ogg": "audio", "flac": "audio",
    "mp4": "video", "m4v": "video", "mov": "video", "webm": "video",
}

# Der Browser entscheidet nach dem Content-Type; hochgeladene Dateien kommen oft als „octet-stream“ an.
MEDIA = {
    "pdf": "application/pdf", "txt": "text/plain; charset=utf-8", "md": "text/plain; charset=utf-8",
    "markdown": "text/plain; charset=utf-8",
    "png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg", "webp": "image/webp", "gif": "image/gif",
    "mp3": "audio/mpeg", "m4a": "audio/mp4", "aac": "audio/aac", "wav": "audio/wav", "ogg": "audio/ogg", "flac": "audio/flac",
    "mp4": "video/mp4", "m4v": "video/mp4", "mov": "video/quicktime", "webm": "video/webm",
}

# Wird beim Hochladen in JPEG umgewandelt (Browser und Texterkennung können sie nicht alle lesen)
UMZUWANDELN = ("heic", "heif")


def endung(dateiname: str) -> str:
    return dateiname.rsplit(".", 1)[-1].lower() if "." in dateiname else ""


def art(dateiname: str) -> str:
    return ENDUNGEN.get(endung(dateiname), "sonst")


def media_type(dateiname: str, gespeichert: str | None) -> str:
    return MEDIA.get(endung(dateiname)) or gespeichert or "application/octet-stream"


def kann_fragen(dateiname: str) -> bool:
    return art(dateiname) in ("pdf", "docx", "pages", "text", "ansichtstext", "bild")
