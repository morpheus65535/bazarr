from types import SimpleNamespace


def test_sports_subtitle_refreshes_matching_plex_section_and_jellyfin_path(monkeypatch):
    from sportarr import media_refresh

    calls = []
    matching = SimpleNamespace(
        locations=['/media/sports'],
        update=lambda path: calls.append(('plex', path)),
    )
    unrelated = SimpleNamespace(
        locations=['/media/movies'],
        update=lambda path: calls.append(('wrong plex', path)),
    )
    server = SimpleNamespace(library=SimpleNamespace(sections=lambda: [unrelated, matching]))
    jellyfin = SimpleNamespace(
        get_libraries=lambda: [{'Locations': ['/media/sports']}],
        report_media_updated=lambda path: calls.append(('jellyfin', path)),
    )
    monkeypatch.setattr(media_refresh, 'settings', SimpleNamespace(
        general=SimpleNamespace(use_plex=True, use_jellyfin=True),
        plex=SimpleNamespace(update_series_library=True),
        jellyfin=SimpleNamespace(update_series_library=True),
    ))
    monkeypatch.setattr(media_refresh, 'path_mappings', SimpleNamespace(
        path_replace_reverse_sports=lambda path: '/media/sports/race.mkv'))
    monkeypatch.setattr(media_refresh, 'get_plex_server', lambda: server)
    monkeypatch.setattr(media_refresh, 'get_jellyfin_client', lambda: jellyfin)

    media_refresh.refresh_sports_media_servers('/bazarr/race.mkv')

    assert calls == [('plex', '/media/sports'), ('jellyfin', '/media/sports/race.mkv')]


def test_sports_subtitle_does_not_scan_unrelated_plex_library(monkeypatch):
    from sportarr import media_refresh

    calls = []
    section = SimpleNamespace(locations=['/media/movies'], update=lambda path: calls.append(path))
    server = SimpleNamespace(library=SimpleNamespace(sections=lambda: [section]))
    monkeypatch.setattr(media_refresh, 'settings', SimpleNamespace(
        general=SimpleNamespace(use_plex=True, use_jellyfin=False),
        plex=SimpleNamespace(update_series_library=True),
    ))
    monkeypatch.setattr(media_refresh, 'path_mappings', SimpleNamespace(
        path_replace_reverse_sports=lambda path: '/media/sports/race.mkv'))
    monkeypatch.setattr(media_refresh, 'get_plex_server', lambda: server)

    media_refresh.refresh_sports_media_servers('/bazarr/race.mkv')

    assert calls == []


def test_sports_subtitle_uses_local_path_when_servers_do_not_share_sportarr_mount(monkeypatch):
    from sportarr import media_refresh

    calls = []
    section = SimpleNamespace(locations=['/bazarr'], update=lambda path: calls.append(('plex', path)))
    server = SimpleNamespace(library=SimpleNamespace(sections=lambda: [section]))
    jellyfin = SimpleNamespace(
        get_libraries=lambda: [{'Locations': ['/bazarr']}],
        report_media_updated=lambda path: calls.append(('jellyfin', path)),
    )
    monkeypatch.setattr(media_refresh, 'settings', SimpleNamespace(
        general=SimpleNamespace(use_plex=True, use_jellyfin=True),
        plex=SimpleNamespace(update_series_library=True),
        jellyfin=SimpleNamespace(update_series_library=True),
    ))
    monkeypatch.setattr(media_refresh, 'path_mappings', SimpleNamespace(
        path_replace_reverse_sports=lambda path: '/media/sports/race.mkv'))
    monkeypatch.setattr(media_refresh, 'get_plex_server', lambda: server)
    monkeypatch.setattr(media_refresh, 'get_jellyfin_client', lambda: jellyfin)

    media_refresh.refresh_sports_media_servers('/bazarr/race.mkv')

    assert calls == [('plex', '/bazarr'), ('jellyfin', '/bazarr/race.mkv')]
