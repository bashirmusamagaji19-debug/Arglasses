from __future__ import annotations

from pathlib import Path
from typing import Protocol


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
) -> str | None:
    if uploaded_file is None:
        return None

    target_dir = Path(upload_dir)
    target_dir.mkdir(parents=True, exist_ok=True)

    filename = Path(getattr(uploaded_file, "name", None) or getattr(uploaded_file, "filename", "")).name
    filename = filename or "camera_capture.jpg"
    target = target_dir / filename
    if hasattr(uploaded_file, "getbuffer"):
        target.write_bytes(uploaded_file.getbuffer())
    else:
        file_obj = getattr(uploaded_file, "file")
        file_obj.seek(0)
        target.write_bytes(file_obj.read())
    return str(target)
