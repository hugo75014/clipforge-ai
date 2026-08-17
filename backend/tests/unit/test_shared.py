"""Unit tests for `shared` utilities."""

from __future__ import annotations

import pytest

from shared.utils import (
    Timer,
    chunked,
    clamp,
    dig,
    estimate_words,
    format_duration,
    format_timestamp,
    is_uuid,
    safe_filename,
    sha256_file,
    short_id,
    slugify,
)


def test_format_duration():
    assert format_duration(0) == "00:00.0"
    assert format_duration(42) == "00:42.0"
    assert format_duration(3725) == "01:02:05"


def test_format_timestamp():
    assert format_timestamp(0) == "00:00:00,000"
    assert format_timestamp(65.5) == "00:01:05,500"


def test_clamp():
    assert clamp(5, 0, 10) == 5
    assert clamp(-1, 0, 10) == 0
    assert clamp(11, 0, 10) == 10


def test_slugify():
    assert slugify("Hello World!") == "hello-world"
    # non-ascii chars are folded to ascii (no separator inserted between)
    assert slugify("Éàï") == "eai"
    assert slugify("") == "untitled"
    assert slugify("Hello, World!") == "hello-world"
    assert slugify("a   b   c") == "a-b-c"


def test_safe_filename():
    assert safe_filename("../../etc/passwd") == "passwd"
    assert safe_filename("normal.mp4") == "normal.mp4"
    assert safe_filename("a" * 200 + ".mp4").endswith(".mp4")


def test_estimate_words():
    assert estimate_words("Hello world!") == 2
    assert estimate_words("") == 0


def test_short_id_is_unique():
    a = short_id("clip")
    b = short_id("clip")
    assert a != b
    assert a.startswith("clip_")


def test_is_uuid():
    assert is_uuid("00000000-0000-0000-0000-000000000000")
    assert not is_uuid("not-a-uuid")


def test_chunked():
    assert list(chunked([1, 2, 3, 4, 5], 2)) == [[1, 2], [3, 4], [5]]


def test_dig():
    payload = {"a": {"b": {"c": 42}}}
    assert dig(payload, "a", "b", "c") == 42
    assert dig(payload, "a", "missing", default="x") == "x"


def test_timer():
    with Timer() as t:
        pass
    assert t.elapsed >= 0


def test_sha256_file(tmp_path):
    p = tmp_path / "a.txt"
    p.write_bytes(b"hello")
    assert sha256_file(p) == "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"
