import io
import tempfile
import pytest
from py7zr import SevenZipFile
from subliminal_patch.providers.zimuku import (
    SevenZipArchive,
    _get_subtitle_from_archive,
)


@pytest.fixture
def sample_7z_bytes():
    buf = io.BytesIO()
    with tempfile.NamedTemporaryFile(suffix=".srt") as f1, \
         tempfile.NamedTemporaryFile(suffix=".ass") as f2, \
         tempfile.NamedTemporaryFile(suffix=".txt") as f3:
        f1.write(b"1\n00:00:01,000 --> 00:00:04,000\nHello Simplified\n")
        f1.flush()
        f2.write(b"[Script Info]\nTitle: Traditional\n")
        f2.flush()
        f3.write(b"Visit zimuku.org for more subtitles\n")
        f3.flush()

        with SevenZipFile(buf, "w") as z:
            z.write(f1.name, "Test.Show.S01E01.1080p.简英.srt")
            z.write(f2.name, "Test.Show.S01E01.1080p.繁体.ass")
            z.write(f3.name, "readme.txt")

    return buf.getvalue()


def test_seven_zip_archive_namelist_and_read(sample_7z_bytes):
    with SevenZipArchive(sample_7z_bytes) as archive:
        names = archive.namelist()
        assert len(names) == 3
        assert "Test.Show.S01E01.1080p.简英.srt" in names
        assert "Test.Show.S01E01.1080p.繁体.ass" in names
        assert "readme.txt" in names

        chs_content = archive.read("Test.Show.S01E01.1080p.简英.srt")
        assert chs_content is not None
        assert b"Hello Simplified" in chs_content

        cht_content = archive.read("Test.Show.S01E01.1080p.繁体.ass")
        assert cht_content is not None
        assert b"Title: Traditional" in cht_content

        assert archive.read("nonexistent.srt") is None


def test_get_subtitle_from_7z_archive(sample_7z_bytes):
    with SevenZipArchive(sample_7z_bytes) as archive:
        content = _get_subtitle_from_archive(archive)
        assert content is not None
        # Should prefer bilingual '简英' (score: ass/srt (1) + 简英 (4) = 5) over '繁体' (score 3)
        assert b"Hello Simplified" in content


def test_seven_zip_archive_from_stream(sample_7z_bytes):
    stream = io.BytesIO(sample_7z_bytes)
    with SevenZipArchive(stream) as archive:
        names = archive.namelist()
        assert len(names) == 3
        content = archive.read("Test.Show.S01E01.1080p.简英.srt")
        assert b"Hello Simplified" in content
