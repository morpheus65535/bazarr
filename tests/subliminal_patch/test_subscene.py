from subliminal_patch.providers import subscene_cloudscraper as subscene


def test_provider_scraper_call():
    with subscene.SubsceneProvider() as provider:
        result = provider._scraper_call(
            "https://subscene.com/subtitles/breaking-bad-fifth-season"
        )
        assert result.status_code == 200


def test_provider_gen_results():
    with subscene.SubsceneProvider() as provider:
        assert list(provider._gen_results("Breaking Bad"))


def test_provider_search_movie():
    with subscene.SubsceneProvider() as provider:
        result = provider._search_movie("Taxi Driver", 1976)
        assert result == "/subtitles/taxi-driver"


def test_provider_find_movie_subtitles(languages):
    with subscene.SubsceneProvider() as provider:
        result = provider._find_movie_subtitles(
            "/subtitles/taxi-driver", languages["en"]
        )
        assert result


def test_provider_search_tv_show_season():
    with subscene.SubsceneProvider() as provider:
        result = provider._search_tv_show_season("The Wire", 1)
        assert result == "/subtitles/the-wire--first-season"


def test_provider_find_episode_subtitles(languages):
    with subscene.SubsceneProvider() as provider:
        result = provider._find_episode_subtitles(
            "/subtitles/the-wire--first-season", 1, 1, languages["en"]
        )
        assert result


def test_provider_download_subtitle(languages):
    path = "https://subscene.com/subtitles/the-wire--first-season/english/115904"
    subtitle = subscene.SubsceneSubtitle(languages["en"], path, "", 1)
    with subscene.SubsceneProvider() as provider:
        provider.download_subtitle(subtitle)
        assert subtitle.is_valid()
