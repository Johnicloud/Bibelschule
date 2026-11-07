"""Ausgehender Adapter: HEIC/HEIF (iPhone-Fotos) -> JPEG mit Pillow + pillow-heif."""
import io

from app.application.ports import BildWandler
from app.domain.errors import InvalidInput


class PillowBildWandler(BildWandler):
    def zu_jpeg(self, inhalt: bytes) -> bytes:
        try:
            from PIL import Image, ImageOps
            from pillow_heif import register_heif_opener
            register_heif_opener()
            bild = ImageOps.exif_transpose(Image.open(io.BytesIO(inhalt))).convert("RGB")   # Drehung aus dem Foto übernehmen
            aus = io.BytesIO()
            bild.save(aus, "JPEG", quality=92)
            return aus.getvalue()
        except Exception as e:
            raise InvalidInput("Das Foto (HEIC) ließ sich nicht umwandeln.") from e
