from io import BytesIO

from ai_glasses_memory.services.uploads import save_input_image


class FakeUploadedFile(BytesIO):
    def __init__(self, name: str, content: bytes) -> None:
        super().__init__(content)
        self.name = name

    def getbuffer(self) -> memoryview:
        return memoryview(self.getvalue())


def test_save_input_image_returns_none_when_no_image(tmp_path):
    assert save_input_image(None, upload_dir=tmp_path) is None


def test_save_input_image_persists_uploaded_image(tmp_path):
    image = FakeUploadedFile("desk.jpg", b"fake-image")

    saved_path = save_input_image(image, upload_dir=tmp_path)

    assert saved_path is not None
    assert saved_path.endswith("desk.jpg")
    assert (tmp_path / "desk.jpg").read_bytes() == b"fake-image"


def test_save_input_image_uses_default_name_for_camera_capture(tmp_path):
    image = FakeUploadedFile("", b"camera-frame")

    saved_path = save_input_image(image, upload_dir=tmp_path)

    assert saved_path is not None
    assert saved_path.endswith("camera_capture.jpg")
    assert (tmp_path / "camera_capture.jpg").read_bytes() == b"camera-frame"
