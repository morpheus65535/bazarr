from types import SimpleNamespace

def test_sportarr_browser_keeps_a_selected_folder_on_unix():
    from sportarr import filesystem

    assert filesystem.folder_browser_path('/media/sports/Main Card') == '/media/sports/Main Card/'


def test_sportarr_browser_keeps_a_selected_folder_on_windows():
    from sportarr import filesystem

    assert filesystem.folder_browser_path('C:\\Sports\\Main Card') == 'C:\\Sports\\Main Card\\'


def test_sportarr_browser_encodes_special_path_characters(monkeypatch):
    from sportarr import filesystem

    calls = []

    def fake_get(url, **kwargs):
        calls.append((url, kwargs))
        return SimpleNamespace(raise_for_status=lambda: None, json=lambda: {'directories': []})

    monkeypatch.setattr(filesystem.requests, 'get', fake_get)
    monkeypatch.setattr(filesystem, 'url_api_sportarr', lambda: 'http://sportarr/api/')
    monkeypatch.setattr(filesystem, 'settings', SimpleNamespace(sportarr=SimpleNamespace(
        apikey='key#1', http_timeout=10,
    )))

    result = filesystem.browse_sportarr_filesystem('/media/A & B #1')

    assert result == {'directories': []}
    assert calls[0][0] == 'http://sportarr/api/filesystem'
    assert calls[0][1]['params'] == {
        'path': '/media/A & B #1', 'includeFiles': 'false', 'apikey': 'key#1',
    }
