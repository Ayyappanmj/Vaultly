import hashlib
import os
import uuid
from abc import ABC, abstractmethod
from pathlib import Path
from fastapi import HTTPException, UploadFile, status

from app.core.config import settings

ALLOWED_MIME_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "application/pdf": ".pdf",
}

MAX_FILE_SIZE_BYTES = 15 * 1024 * 1024  # 15 MB


class StorageService(ABC):
    @abstractmethod
    def save_file(
        self, file_content: bytes, filename: str, user_id: uuid.UUID
    ) -> tuple[str, str, int]:
        """Saves file and returns (relative_file_path, sha256_hash, file_size)."""
        pass

    @abstractmethod
    def get_file_bytes(self, file_path: str, user_id: uuid.UUID) -> bytes:
        """Retrieves file bytes with user isolation check."""
        pass

    @abstractmethod
    def delete_file(self, file_path: str, user_id: uuid.UUID) -> bool:
        """Deletes file with user isolation check."""
        pass


class LocalStorageService(StorageService):
    def __init__(self, base_dir: str | None = None):
        self.base_dir = Path(base_dir or settings.upload_dir).resolve()
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def validate_file(self, file: UploadFile, content: bytes) -> str:
        if len(content) > MAX_FILE_SIZE_BYTES:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File exceeds maximum allowed size of {MAX_FILE_SIZE_BYTES // (1024 * 1024)} MB.",
            )

        mime_type = file.content_type or ""
        if mime_type not in ALLOWED_MIME_TYPES:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail=f"Unsupported file type '{mime_type}'. Allowed: JPEG, PNG, WEBP, PDF.",
            )
        return mime_type

    def save_file(
        self, file_content: bytes, filename: str, user_id: uuid.UUID
    ) -> tuple[str, str, int]:
        file_hash = hashlib.sha256(file_content).hexdigest()
        ext = os.path.splitext(filename)[1].lower() or ".bin"
        safe_filename = f"{uuid.uuid4().hex}{ext}"

        user_folder = self.base_dir / str(user_id)
        user_folder.mkdir(parents=True, exist_ok=True)

        target_path = user_folder / safe_filename
        target_path.write_bytes(file_content)

        relative_path = f"{user_id}/{safe_filename}"
        return relative_path, file_hash, len(file_content)

    def get_file_bytes(self, file_path: str, user_id: uuid.UUID) -> bytes:
        # Prevent directory traversal attacks
        full_path = (self.base_dir / file_path).resolve()
        user_folder = (self.base_dir / str(user_id)).resolve()

        if not full_path.is_relative_to(user_folder):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to requested file.",
            )

        if not full_path.exists() or not full_path.is_file():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found.",
            )

        return full_path.read_bytes()

    def delete_file(self, file_path: str, user_id: uuid.UUID) -> bool:
        full_path = (self.base_dir / file_path).resolve()
        user_folder = (self.base_dir / str(user_id)).resolve()

        if not full_path.is_relative_to(user_folder):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to requested file.",
            )

        if full_path.exists() and full_path.is_file():
            full_path.unlink()
            return True
        return False


storage_service = LocalStorageService()
