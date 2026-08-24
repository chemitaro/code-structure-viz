from __future__ import annotations

import contextlib
import os
import shutil
import stat
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path


def render_text(text: str, replacements: dict[str, str]) -> str:
    rendered = text
    for key, value in replacements.items():
        rendered = rendered.replace(key, value)
    return rendered


def load_template_text(src_path: Path) -> str:
    if not src_path.exists() or not src_path.is_file():
        raise RuntimeError(f"Missing template file: {src_path}")
    try:
        return src_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise RuntimeError(f"Failed to read template: {src_path}: {exc}") from exc


def _template_files(src_dir: Path) -> list[Path]:
    files: list[Path] = []
    for path in sorted(src_dir.rglob("*"), key=lambda p: p.as_posix()):
        if path.is_file():
            files.append(path)
    return files


def _preflight_no_collision(target_paths: list[Path]) -> None:
    for path in target_paths:
        if path.exists():
            raise RuntimeError(f"Destination already exists: {path}")


def _open_directory_at(parent_fd: int, name: str, *, create: bool) -> int:
    if create:
        with contextlib.suppress(FileExistsError):
            os.mkdir(name, dir_fd=parent_fd)
    return os.open(
        name,
        os.O_RDONLY | os.O_DIRECTORY | getattr(os, "O_NOFOLLOW", 0),
        dir_fd=parent_fd,
    )


def _open_parent_at(root_fd: int, parts: tuple[str, ...], *, create: bool) -> int | None:
    current_fd = os.dup(root_fd)
    try:
        for part in parts:
            try:
                next_fd = _open_directory_at(current_fd, part, create=create)
            except FileNotFoundError:
                if create:
                    raise
                os.close(current_fd)
                return None
            os.close(current_fd)
            current_fd = next_fd
        return current_fd
    except Exception:
        with contextlib.suppress(OSError):
            os.close(current_fd)
        raise


def _write_all(descriptor: int, payload: bytes) -> None:
    offset = 0
    while offset < len(payload):
        written = os.write(descriptor, payload[offset:])
        if written == 0:
            raise OSError("short scaffold write")
        offset += written


def _preflight_no_collision_at(dest_dir_fd: int, rel_files: list[Path], dest_dir: Path) -> None:
    for rel_path in rel_files:
        parent_fd = _open_parent_at(dest_dir_fd, rel_path.parts[:-1], create=False)
        if parent_fd is None:
            continue
        try:
            try:
                os.stat(rel_path.name, dir_fd=parent_fd, follow_symlinks=False)
            except FileNotFoundError:
                continue
            raise RuntimeError(f"Destination already exists: {dest_dir / rel_path}")
        finally:
            os.close(parent_fd)


def copy_scaffolded_tree_at(
    src_dir: Path,
    dest_dir: Path,
    dest_dir_fd: int,
    replacements: dict[str, str],
) -> list[Path]:
    """Copy a scaffold through a held destination directory descriptor."""
    if not src_dir.exists() or not src_dir.is_dir():
        raise RuntimeError(f"Missing template directory: {src_dir}")

    template_files = _template_files(src_dir)
    rel_files = [path.relative_to(src_dir) for path in template_files]
    _preflight_no_collision_at(dest_dir_fd, rel_files, dest_dir)

    created_paths: list[Path] = []
    for src_path, rel_path in zip(template_files, rel_files, strict=True):
        source_bytes = src_path.read_bytes()
        is_shebang = False
        try:
            text = source_bytes.decode("utf-8")
        except UnicodeDecodeError:
            rendered_bytes = source_bytes
            target_mode = stat.S_IMODE(src_path.stat().st_mode)
            preserve_source_metadata = True
        else:
            rendered_bytes = render_text(text, replacements).encode("utf-8")
            is_shebang = text.startswith("#!")
            preserve_source_metadata = rendered_bytes == source_bytes
            target_mode = stat.S_IMODE(src_path.stat().st_mode) if preserve_source_metadata else 0o666
        parent_fd = _open_parent_at(dest_dir_fd, rel_path.parts[:-1], create=True)
        assert parent_fd is not None
        try:
            target_fd = os.open(
                rel_path.name,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL,
                target_mode,
                dir_fd=parent_fd,
            )
            try:
                _write_all(target_fd, rendered_bytes)
                if preserve_source_metadata:
                    source_stat = src_path.stat()
                    os.fchmod(target_fd, stat.S_IMODE(source_stat.st_mode))
                    os.utime(target_fd, ns=(source_stat.st_atime_ns, source_stat.st_mtime_ns))
                if is_shebang:
                    os.fchmod(target_fd, stat.S_IMODE(os.fstat(target_fd).st_mode) | 0o111)
            finally:
                os.close(target_fd)
        finally:
            os.close(parent_fd)
        created_paths.append(dest_dir / rel_path)
    return created_paths


def copy_scaffolded_tree(src_dir: Path, dest_dir: Path, replacements: dict[str, str]) -> list[Path]:
    if not src_dir.exists() or not src_dir.is_dir():
        raise RuntimeError(f"Missing template directory: {src_dir}")

    template_files = _template_files(src_dir)
    rel_files = [path.relative_to(src_dir) for path in template_files]
    target_paths = [dest_dir / rel for rel in rel_files]
    _preflight_no_collision(target_paths)

    created_paths: list[Path] = []
    for src_path, target_path in zip(template_files, target_paths, strict=True):
        target_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            source_bytes = src_path.read_bytes()
            text = source_bytes.decode("utf-8")
        except UnicodeDecodeError:
            shutil.copy2(src_path, target_path)
        else:
            rendered_bytes = render_text(text, replacements).encode("utf-8")
            if rendered_bytes == source_bytes:
                shutil.copy2(src_path, target_path)
            else:
                target_path.write_bytes(rendered_bytes)
            if text.startswith("#!"):
                with contextlib.suppress(OSError):
                    target_path.chmod(target_path.stat().st_mode | 0o111)
        created_paths.append(target_path)
    return created_paths


def write_text(dest_path: Path, text: str) -> None:
    if dest_path.exists():
        raise RuntimeError(f"Destination already exists: {dest_path}")
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    dest_path.write_text(text, encoding="utf-8")
