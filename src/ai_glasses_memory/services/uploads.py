from __future__ import annotations

import logging
from io import BytesIO
from pathlib import Path
from typing import Protocol


logger = logging.getLogger(__name__)


class UploadedImage(Protocol):
    name: str

    def getbuffer(self) -> memoryview:
        ...


class FastAPIUploadFile(Protocol):
    filename: str | None
    file: object


def save_input_image(
    uploaded_file: UploadedImage | None,
    upload_dir: str | Path = "data/uploads",
    max_side: int = 1600,
) -> str | None:
    if uploaded_file is None:
        return None

    target_dir = Path(upload_dir)
    target_dir.mkdir(parents=True, exist_ok=True)

    filename = Path(getattr(uploaded_file, "name", None) or getattr(uploaded_file, "filename", "")).name
    filename = filename or "camera_capture.jpg"
    original_bytes = _read_upload_bytes(uploaded_file)
    saved_bytes, compressed = _compress_image_bytes(original_bytes, max_side=max_side)
    if compressed:
        filename = Path(filename).with_suffix(".jpg").name

    target = target_dir / filename
    target.write_bytes(saved_bytes)
    return str(target)


def _read_upload_bytes(uploaded_file) -> bytes:
    if hasattr(uploaded_file, "getbuffer"):
        return bytes(uploaded_file.getbuffer())

    file_obj = getattr(uploaded_file, "file")
    file_obj.seek(0)
    return file_obj.read()


def _compress_image_bytes(image_bytes: bytes, max_side: int) -> tuple[bytes, bool]:
    try:
        from PIL import Image

        with Image.open(BytesIO(image_bytes)) as image:
            image = image.convert("RGB")
            original_size = image.size
            longest_side = max(image.size)
            if longest_side > max_side:
                ratio = max_side / longest_side
                image = image.resize((max(1, int(image.width * ratio)), max(1, int(image.height * ratio))))

            buffer = BytesIO()
            image.save(buffer, format="JPEG", quality=85, optimize=True)
            compressed_bytes = buffer.getvalue()
            logger.info(
                "Uploaded image prepared: original_size=%s saved_size=%s bytes=%s",
                original_size,
                image.size,
                len(compressed_bytes),
            )
            return compressed_bytes, True
    except Exception as exc:
        logger.warning("Uploaded image compression skipped: error=%s", exc)
        return image_bytes, False
