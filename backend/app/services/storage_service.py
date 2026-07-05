from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile


class StorageService:
    """
    Handles file storage.

    Initially stores files locally.
    Later this implementation will be replaced
    with Google Cloud Storage.
    """

    def __init__(self):
        self.upload_dir = Path("uploads")
        self.upload_dir.mkdir(
            exist_ok=True
        )

    async def save(
        self,
        file: UploadFile,
    ) -> tuple[str, str]:

        extension = Path(file.filename).suffix

        filename = (
            f"{uuid4()}{extension}"
        )

        destination = (
            self.upload_dir / filename
        )

        with open(destination, "wb") as buffer:
            buffer.write(await file.read())

        return (
            filename,
            str(destination),
        )