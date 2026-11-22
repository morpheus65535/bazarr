import io
import tempfile
import pytest
from PIL import Image
from py7zr import SevenZipFile
from subliminal_patch.providers.zimuku import (
    SevenZipArchive,
    _CAPTCHA_SLOT_WIDTH,
    _DIGIT_TEMPLATES,
    _get_subtitle_from_archive,
    solve_bmp_captcha,
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


def _make_test_captcha(code):
    img = Image.new("RGB", (100, 30), color=(255, 255, 255))
    pixels = img.load()
    for d_idx, char in enumerate(code):
        w, rows = _DIGIT_TEMPLATES[char]
        start_x = d_idx * _CAPTCHA_SLOT_WIDTH + 5
        start_y = 8
        for y, row_bits in enumerate(rows):
            for x in range(w):
                if (row_bits >> (w - 1 - x)) & 1:
                    pixels[start_x + x, start_y + y] = (10, 180, 20)
    buf = io.BytesIO()
    img.save(buf, format="BMP")
    return buf.getvalue()


def test_solve_bmp_captcha():
    assert solve_bmp_captcha(_make_test_captcha("58219")) == "58219"
    assert solve_bmp_captcha(_make_test_captcha("01234")) == "01234"
    assert solve_bmp_captcha(_make_test_captcha("96780")) == "96780"


def test_solve_bmp_captcha_invalid():
    assert solve_bmp_captcha(b"") is None
    assert solve_bmp_captcha(b"not an image") is None
    blank = Image.new("RGB", (100, 30), color=(255, 255, 255))
    buf = io.BytesIO()
    blank.save(buf, format="BMP")
    assert solve_bmp_captcha(buf.getvalue()) is None



class _FakeResponse:
    def __init__(self, status_code, text, url):
        self.status_code = status_code
        self.text = text
        self.url = url
        self.content = text.encode("utf-8")


class _FakeSession:
    def __init__(self, response):
        from requests.cookies import RequestsCookieJar
        self.response = response
        self.cookies = RequestsCookieJar()
        self.calls = 0

    def get(self, url, *args, **kwargs):
        self.calls += 1
        return self.response


def _challenge_html():
    import base64
    buf = io.BytesIO()
    # Blank image: the local solver finds no strokes and returns None.
    Image.new("RGB", (100, 30), (0, 0, 0)).save(buf, "BMP")
    b64 = base64.b64encode(buf.getvalue()).decode("ascii")
    return f'<html><img src="data:image/bmp;base64,{b64}"></html>'


def _install_paid_stub(monkeypatch, results):
    """Replace the DBC pitcher with a real Pitcher subclass returning ``results`` in order."""
    import subliminal_patch.pitcher as pitcher_module
    import subliminal_patch.providers.zimuku as zimuku

    class FakePitcher(pitcher_module.Pitcher):
        name = "DeathByCaptchaImageToText"
        instances = []
        decodes = 0

        def __init__(self, website_name, image_fp, tries=3, *args, **kwargs):
            self.website_name = website_name
            self.tries = tries
            self.solve_time = None
            FakePitcher.instances.append(self)

        def _throw(self):
            FakePitcher.decodes += 1
            return results.pop(0) if results else None

    class FakeRegistry:
        def get_pitcher(self, name):
            assert name == "DeathByCaptchaImageToText"
            return FakePitcher

    monkeypatch.setenv("ANTICAPTCHA_CLASS", "DeathByCaptchaProxyLess")
    monkeypatch.setattr(zimuku, "pitchers", FakeRegistry())
    monkeypatch.setattr(pitcher_module, "_solve_cooldowns", {})
    return FakePitcher


def test_yunsuo_bypass_makes_at_most_one_paid_attempt_per_call(monkeypatch):
    import subliminal_patch.providers.zimuku as zimuku
    FakePitcher = _install_paid_stub(monkeypatch, [None])

    provider = zimuku.ZimukuProvider()
    provider.session = _FakeSession(_FakeResponse(404, _challenge_html(), "https://zimuku.org/x"))
    provider.yunsuo_bypass("https://zimuku.org/x")

    # Six challenge attempts were served, but only one paid decode was made, with no internal retries.
    assert provider.session.calls == zimuku._MAX_YUNSUO_RETRIES
    assert FakePitcher.decodes == 1
    assert FakePitcher.instances[0].tries == 1


def test_rejected_paid_answer_pauses_paid_solving(monkeypatch):
    import subliminal_patch.providers.zimuku as zimuku
    # The paid service returns an answer, but the server keeps serving the challenge.
    FakePitcher = _install_paid_stub(monkeypatch, ["11111", "22222"])

    provider = zimuku.ZimukuProvider()
    provider.session = _FakeSession(_FakeResponse(404, _challenge_html(), "https://zimuku.org/x"))
    provider.yunsuo_bypass("https://zimuku.org/x")
    assert FakePitcher.decodes == 1

    # The next call must not pay again while the rejected answer's cooldown is active.
    provider.yunsuo_bypass("https://zimuku.org/x")
    assert FakePitcher.decodes == 1


def test_accepted_paid_answer_does_not_pause_paid_solving(monkeypatch):
    import subliminal_patch.providers.zimuku as zimuku
    FakePitcher = _install_paid_stub(monkeypatch, ["11111"])

    challenge = (_challenge_html()[:-len("</html>")]
                 + "<script>self.location = \"/verify?\" + stringToHex(</script></html>")
    provider = zimuku.ZimukuProvider()
    responses = [_FakeResponse(404, challenge, "https://zimuku.org/x"),
                 _FakeResponse(200, "<html>ok</html>", "https://zimuku.org/x")]

    class SeqSession(_FakeSession):
        def get(self, url, *args, **kwargs):
            self.calls += 1
            return responses.pop(0) if len(responses) > 1 else responses[0]

    provider.session = SeqSession(responses[0])
    provider.yunsuo_bypass("https://zimuku.org/x")
    assert FakePitcher.decodes == 1
    assert zimuku.get_solve_cooldown("DeathByCaptchaImageToText").is_available() is True
