"""File operation utilities."""

import os
import logging
from pathlib import Path
from typing import Optional, Union


def ensure_data_directory(path: Union[str, Path] = "./data") -> str:
    """Ensure data directory exists.

    Args:
        path: Directory path (default: ./data)

    Returns:
        Path to data directory as string
    """
    data_dir = Path(path).expanduser().resolve()
    data_dir.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger(__name__)
    logger.debug("Data directory ensured", extra={"path": str(data_dir)})
    return str(data_dir)


def read_file_safe(
    filepath: Union[str, Path],
    encoding: str = "utf-8",
    fallback_encoding: str = "latin-1",
) -> str:
    """Read file with encoding fallback.

    Args:
        filepath: Path to file
        encoding: Primary encoding to try
        fallback_encoding: Fallback encoding if primary fails

    Returns:
        File content as string

    Raises:
        FileNotFoundError: If file doesn't exist
        IOError: If reading fails
    """
    path = Path(filepath)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {filepath}")

    try:
        content = path.read_text(encoding=encoding)
        return content
    except UnicodeDecodeError:
        # Try fallback encoding
        try:
            content = path.read_text(encoding=fallback_encoding)
            return content
        except Exception as e:
            raise IOError(
                f"Failed to read {filepath} with encodings "
                f"{encoding} and {fallback_encoding}: {e}"
            ) from e
    except Exception as e:
        raise IOError(f"Failed to read {filepath}: {e}") from e


def get_file_size(filepath: Union[str, Path]) -> int:
    """Get file size in bytes.

    Args:
        filepath: Path to file

    Returns:
        File size in bytes
    """
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {filepath}")
    return path.stat().st_size


def is_safe_filepath(filepath: Union[str, Path], base_dir: Union[str, Path]) -> bool:
    """Check if filepath is within base_dir (security check).

    Args:
        filepath: Path to check
        base_dir: Base directory that should contain the file

    Returns:
        True if filepath is safe (within base_dir)
    """
    path = Path(filepath).resolve()
    base = Path(base_dir).resolve()

    try:
        path.relative_to(base)
        return True
    except ValueError:
        return False


def list_files(
    directory: Union[str, Path],
    pattern: Optional[str] = None,
    recursive: bool = False,
) -> list:
    """List files in directory.

    Args:
        directory: Directory to list
        pattern: Optional glob pattern (e.g., "*.txt")
        recursive: Whether to search recursively

    Returns:
        List of Path objects
    """
    import glob

    dir_path = Path(directory)

    if not dir_path.exists():
        return []

    if pattern:
        search_pattern = str(dir_path / pattern)
        files = glob.glob(search_pattern, recursive=recursive)
        return [Path(f) for f in files if Path(f).is_file()]
    else:
        if recursive:
            return [p for p in dir_path.rglob("*") if p.is_file()]
        else:
            return [p for p in dir_path.iterdir() if p.is_file()]
