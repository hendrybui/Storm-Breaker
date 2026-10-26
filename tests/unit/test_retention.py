"""Unit tests for ``app.core.retention`` (P7.5 — capture-dir rotation)."""
import os
import time

from app.core.retention import rotate_capture_dirs


def make_file(path, age_days):
    path.write_text('x')
    old = time.time() - age_days * 86400 - 10
    os.utime(path, (old, old))


def test_rotates_only_old_files(tmp_path):
    images = tmp_path / 'images'
    images.mkdir()
    make_file(images / 'old.jpg', 40)
    make_file(images / 'new.jpg', 1)
    removed = rotate_capture_dirs(retention_days=30, base_dir=str(tmp_path),
                                  dirs=('images',), now=time.time())
    assert removed == 1
    assert not (images / 'old.jpg').exists()
    assert (images / 'new.jpg').exists()


def test_multiple_dirs(tmp_path):
    for d in ('images', 'keystrokes'):
        (tmp_path / d).mkdir()
    make_file(tmp_path / 'images' / 'a.png', 90)
    make_file(tmp_path / 'keystrokes' / 'b.json', 90)
    make_file(tmp_path / 'keystrokes' / 'c.json', 0)
    removed = rotate_capture_dirs(retention_days=30, base_dir=str(tmp_path),
                                  dirs=('images', 'keystrokes'),
                                  now=time.time())
    assert removed == 2
    assert not (tmp_path / 'images' / 'a.png').exists()
    assert (tmp_path / 'keystrokes' / 'c.json').exists()


def test_missing_dir_is_ok(tmp_path):
    removed = rotate_capture_dirs(retention_days=30, base_dir=str(tmp_path),
                                  dirs=('does_not_exist',), now=time.time())
    assert removed == 0


def test_subdirectories_never_touched(tmp_path):
    d = tmp_path / 'images'
    d.mkdir()
    (d / 'sub').mkdir()
    make_file(d / 'sub' / 'nested.jpg', 90)
    removed = rotate_capture_dirs(retention_days=30, base_dir=str(tmp_path),
                                  dirs=('images',), now=time.time())
    assert removed == 0  # only top-level files rotate, never recurse
    assert (d / 'sub' / 'nested.jpg').exists()


def test_default_dirs_constant():
    from app.core.retention import DEFAULT_DIRS
    assert {'images', 'sounds', 'videos', 'keystrokes',
            'fingerprints', 'sessions'} <= set(DEFAULT_DIRS)
