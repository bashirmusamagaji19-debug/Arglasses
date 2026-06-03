from __future__ import annotations

from pathlib import Path
from typing import Protocol


class UploadedImage(Protocol):
    name: str

    def getbuffer(self) -> memoryview:
        ...


def save_input_image(
    uploaded_file: UploadedImage | None,
    upload_dir: str | Path = "data/uploads",
) -> str | None:
    if uploaded_file is None:
        return None

    target_dir = Path(upload_dir)
    target_dir.mkdir(parents=True, exist_ok=True)

    filename = Path(uploaded_file.name).name or "camera_capture.jpg"
    target = target_dir / filename
    target.write_bytes(uploaded_file.getbuffer())
    return str(target)
