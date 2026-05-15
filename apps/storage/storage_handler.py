"""
Universal storage handler for cloud-agnostic file operations.

Supports: Local, Azure Blob Storage, AWS S3

Provides CRUD operations (Create, Read, Update, Delete) that work uniformly
across all storage backends configured in Django settings.
"""

from datetime import datetime
from io import BytesIO
import os
from typing import Optional, List, Dict, Any, BinaryIO

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage, staticfiles_storage


class StorageOperationError(Exception):
    """Raised when a storage operation fails."""
    pass


class FileNotFoundError(StorageOperationError):
    """Raised when a file is not found in storage."""
    pass


class StorageFileInfo:
    """Metadata about a stored file."""

    def __init__(
        self,
        name: str,
        size: int,
        created_at: Optional[datetime] = None,
        modified_at: Optional[datetime] = None,
        url: Optional[str] = None,
        storage_backend: str = "unknown",
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.name = name
        self.size = size
        self.created_at = created_at
        self.modified_at = modified_at
        self.url = url
        self.storage_backend = storage_backend
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "size": self.size,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "modified_at": self.modified_at.isoformat() if self.modified_at else None,
            "url": self.url,
            "storage_backend": self.storage_backend,
            "metadata": self.metadata,
        }

    def __repr__(self):
        return f"<StorageFileInfo name={self.name} size={self.size} url={self.url}>"


class StorageHandler:
    """
    Universal file storage handler supporting local, Azure, and S3 backends.

    Example usage:
        handler = StorageHandler()
        handler.upload_file('document.pdf', file_obj)
        file_info = handler.get_file('document.pdf')
        handler.delete_file('document.pdf')
    """

    def __init__(self, storage_type: str = "default"):
        """
        Initialize storage handler.

        Args:
            storage_type: 'default' for media files, 'staticfiles' for static files
        """
        if storage_type not in ("default", "staticfiles"):
            raise ValueError(
                f"storage_type must be 'default' or 'staticfiles', got '{storage_type}'"
            )

        self.storage_type = storage_type
        self.storage = (
            default_storage if storage_type == "default" else staticfiles_storage
        )
        self.backend_name = self._detect_backend()

    def _detect_backend(self) -> str:
        """Detect which storage backend is being used."""
        backend_class = self.storage.__class__.__name__

        if "S3" in backend_class:
            return "s3"
        elif "Azure" in backend_class:
            return "azure"
        else:
            return "local"

    def upload_file(
        self,
        file_path: str,
        file_content: BinaryIO,
        overwrite: bool = True,
        metadata: Optional[Dict[str, str]] = None,
    ) -> StorageFileInfo:
        """
        Upload a file to storage.

        Args:
            file_path: Path/name for the file in storage
            file_content: File-like object or bytes
            overwrite: Whether to overwrite if file exists
            metadata: Optional metadata to attach (S3 only)

        Returns:
            StorageFileInfo with file details

        Raises:
            StorageOperationError: If upload fails
            ValidationError: If file_path is invalid
        """
        if not file_path:
            raise ValidationError("file_path cannot be empty")

        try:
            # Handle both file objects and bytes
            if isinstance(file_content, bytes):
                content = file_content
            else:
                content = file_content.read()

            # Check if file exists and overwrite setting
            if self.storage.exists(file_path) and not overwrite:
                raise StorageOperationError(
                    f"File '{file_path}' already exists and overwrite=False"
                )

            # Save file
            saved_path = self.storage.save(file_path, ContentFile(content))

            # Get file info
            file_info = self._get_file_info(saved_path)
            return file_info

        except Exception as e:
            raise StorageOperationError(f"Failed to upload file '{file_path}': {str(e)}")

    def download_file(self, file_path: str) -> bytes:
        """
        Download/read a file from storage.

        Args:
            file_path: Path to file in storage

        Returns:
            File content as bytes

        Raises:
            FileNotFoundError: If file doesn't exist
            StorageOperationError: If read fails
        """
        if not self.storage.exists(file_path):
            raise FileNotFoundError(f"File '{file_path}' not found in storage")

        try:
            with self.storage.open(file_path, "rb") as f:
                return f.read()
        except Exception as e:
            raise StorageOperationError(f"Failed to download file '{file_path}': {str(e)}")

    def delete_file(self, file_path: str) -> bool:
        """
        Delete a file from storage.

        Args:
            file_path: Path to file in storage

        Returns:
            True if successful, False if file didn't exist

        Raises:
            StorageOperationError: If deletion fails
        """
        if not self.storage.exists(file_path):
            return False

        try:
            self.storage.delete(file_path)
            return True
        except Exception as e:
            raise StorageOperationError(f"Failed to delete file '{file_path}': {str(e)}")

    def file_exists(self, file_path: str) -> bool:
        """Check if a file exists in storage."""
        try:
            return self.storage.exists(file_path)
        except Exception:
            return False

    def get_file(self, file_path: str) -> StorageFileInfo:
        """
        Get file metadata and URL.

        Args:
            file_path: Path to file in storage

        Returns:
            StorageFileInfo with file details

        Raises:
            FileNotFoundError: If file doesn't exist
        """
        if not self.storage.exists(file_path):
            raise FileNotFoundError(f"File '{file_path}' not found in storage")

        return self._get_file_info(file_path)

    def list_files(self, folder_path: str = "") -> List[StorageFileInfo]:
        """
        List all files in a folder/prefix.

        Args:
            folder_path: Folder prefix to list (empty string for root)

        Returns:
            List of StorageFileInfo for each file

        Raises:
            StorageOperationError: If listing fails
        """
        try:
            # Normalize path
            if folder_path and not folder_path.endswith("/"):
                folder_path += "/"

            files = []

            # Different backends have different listing methods
            if self.backend_name == "s3":
                # S3 backend
                from storages.backends.s3boto3 import S3Boto3Storage

                if isinstance(self.storage, S3Boto3Storage):
                    bucket = self.storage.bucket
                    prefix = folder_path
                    for obj in bucket.objects.filter(Prefix=prefix):
                        if not obj.key.endswith("/"):  # Skip folders
                            files.append(self._get_file_info_from_key(obj.key))

            elif self.backend_name == "azure":
                # Azure backend
                from storages.backends.azure_storage import AzureStorage

                if isinstance(self.storage, AzureStorage):
                    container_client = self.storage.client
                    blobs = container_client.list_blobs(name_starts_with=folder_path)
                    for blob in blobs:
                        files.append(self._get_file_info_from_blob(blob))

            else:
                # Local filesystem backend
                base_path = os.path.join(self.storage.location, folder_path)
                if os.path.isdir(base_path):
                    for filename in os.listdir(base_path):
                        filepath = os.path.join(base_path, filename)
                        if os.path.isfile(filepath):
                            rel_path = os.path.relpath(filepath, self.storage.location)
                            files.append(self._get_file_info(rel_path))

            return files

        except Exception as e:
            raise StorageOperationError(f"Failed to list files in '{folder_path}': {str(e)}")

    def search_files(self, pattern: str) -> List[StorageFileInfo]:
        """
        Search for files matching a pattern.

        Args:
            pattern: File pattern/glob (e.g., '*.pdf', 'documents/*')

        Returns:
            List of matching StorageFileInfo objects
        """
        try:
            import fnmatch

            all_files = []

            # Get all files recursively (simplified approach)
            if self.backend_name == "s3":
                from storages.backends.s3boto3 import S3Boto3Storage

                if isinstance(self.storage, S3Boto3Storage):
                    bucket = self.storage.bucket
                    for obj in bucket.objects.all():
                        if not obj.key.endswith("/"):
                            all_files.append(obj.key)

            elif self.backend_name == "azure":
                from storages.backends.azure_storage import AzureStorage

                if isinstance(self.storage, AzureStorage):
                    container_client = self.storage.client
                    for blob in container_client.list_blobs():
                        if not blob.name.endswith("/"):
                            all_files.append(blob.name)

            else:
                # Local filesystem
                for root, dirs, filenames in os.walk(self.storage.location):
                    for filename in filenames:
                        filepath = os.path.join(root, filename)
                        rel_path = os.path.relpath(filepath, self.storage.location)
                        all_files.append(rel_path)

            # Filter by pattern
            matching_files = [f for f in all_files if fnmatch.fnmatch(f, pattern)]

            return [self._get_file_info(f) for f in matching_files]

        except Exception as e:
            raise StorageOperationError(f"Failed to search for pattern '{pattern}': {str(e)}")

    def copy_file(self, source_path: str, dest_path: str, overwrite: bool = True) -> StorageFileInfo:
        """
        Copy a file within storage.

        Args:
            source_path: Source file path
            dest_path: Destination file path
            overwrite: Whether to overwrite if destination exists

        Returns:
            StorageFileInfo for the copied file
        """
        try:
            # Read source
            content = self.download_file(source_path)

            # Write to destination
            return self.upload_file(dest_path, content, overwrite=overwrite)

        except Exception as e:
            raise StorageOperationError(
                f"Failed to copy '{source_path}' to '{dest_path}': {str(e)}"
            )

    def move_file(self, source_path: str, dest_path: str, overwrite: bool = True) -> StorageFileInfo:
        """
        Move a file within storage (copy then delete).

        Args:
            source_path: Source file path
            dest_path: Destination file path
            overwrite: Whether to overwrite if destination exists

        Returns:
            StorageFileInfo for the moved file
        """
        try:
            file_info = self.copy_file(source_path, dest_path, overwrite=overwrite)
            self.delete_file(source_path)
            return file_info
        except Exception as e:
            raise StorageOperationError(
                f"Failed to move '{source_path}' to '{dest_path}': {str(e)}"
            )

    def get_file_size(self, file_path: str) -> int:
        """Get file size in bytes."""
        try:
            return self.storage.size(file_path)
        except Exception:
            return 0

    def get_file_url(self, file_path: str) -> str:
        """Get public URL for a file."""
        try:
            return self.storage.url(file_path)
        except Exception:
            return ""

    def get_file_metadata(self, file_path: str) -> Dict[str, Any]:
        """
        Get metadata for a file (backend-specific).

        Returns:
            Dictionary with metadata (contents vary by backend)
        """
        if self.backend_name == "s3":
            try:
                from storages.backends.s3boto3 import S3Boto3Storage

                if isinstance(self.storage, S3Boto3Storage):
                    bucket = self.storage.bucket
                    obj = bucket.Object(file_path)
                    obj.load()
                    return {
                        "size": obj.content_length,
                        "content_type": obj.content_type,
                        "last_modified": obj.last_modified.isoformat(),
                        "metadata": obj.metadata,
                        "etag": obj.e_tag,
                    }
            except Exception:
                pass

        elif self.backend_name == "azure":
            try:
                from storages.backends.azure_storage import AzureStorage

                if isinstance(self.storage, AzureStorage):
                    container_client = self.storage.client
                    blob_client = container_client.get_blob_client(file_path)
                    properties = blob_client.get_blob_properties()
                    return {
                        "size": properties.size,
                        "content_type": properties.content_settings.content_type,
                        "last_modified": properties.last_modified.isoformat(),
                        "metadata": properties.metadata,
                    }
            except Exception:
                pass

        else:
            # Local filesystem
            try:
                full_path = os.path.join(self.storage.location, file_path)
                if os.path.exists(full_path):
                    stat_info = os.stat(full_path)
                    return {
                        "size": stat_info.st_size,
                        "created": datetime.fromtimestamp(stat_info.st_ctime).isoformat(),
                        "modified": datetime.fromtimestamp(stat_info.st_mtime).isoformat(),
                    }
            except Exception:
                pass

        return {}

    def _get_file_info(self, file_path: str) -> StorageFileInfo:
        """Get StorageFileInfo for a file."""
        try:
            size = self.storage.size(file_path)
            url = self.storage.url(file_path)
            metadata = self.get_file_metadata(file_path)

            return StorageFileInfo(
                name=file_path,
                size=size,
                url=url,
                storage_backend=self.backend_name,
                metadata=metadata,
            )
        except Exception as e:
            raise StorageOperationError(f"Failed to get info for '{file_path}': {str(e)}")

    def _get_file_info_from_key(self, key: str) -> StorageFileInfo:
        """Get StorageFileInfo from S3 key."""
        try:
            from storages.backends.s3boto3 import S3Boto3Storage

            if isinstance(self.storage, S3Boto3Storage):
                bucket = self.storage.bucket
                obj = bucket.Object(key)
                obj.load()
                return StorageFileInfo(
                    name=key,
                    size=obj.content_length,
                    modified_at=obj.last_modified,
                    url=self.storage.url(key),
                    storage_backend="s3",
                    metadata=obj.metadata or {},
                )
        except Exception:
            pass

        return StorageFileInfo(name=key, size=0, storage_backend="s3")

    def _get_file_info_from_blob(self, blob) -> StorageFileInfo:
        """Get StorageFileInfo from Azure blob."""
        try:
            return StorageFileInfo(
                name=blob.name,
                size=blob.size,
                modified_at=blob.last_modified,
                url=f"{self.storage.account_url}/{blob.container_name}/{blob.name}",
                storage_backend="azure",
                metadata=blob.metadata or {},
            )
        except Exception:
            pass

        return StorageFileInfo(name=blob.name, size=0, storage_backend="azure")
