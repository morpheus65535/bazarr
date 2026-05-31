"""
Tests that verify check_login is invoked through Flask's routing layer.

The bug: @check_login is placed ABOVE @ui_bp.route in ui.py. Flask captures
the original function reference before check_login wraps it, making check_login
dead code — auth is never enforced for these routes regardless of configuration.

    # broken: Flask registers original series_images, ignoring the wrapper
    @check_login
    @ui_bp.route('/images/series/<path:url>', methods=['GET'])
    def series_images(url): ...

Fix: @ui_bp.route must be the outermost decorator so Flask registers the
check_login wrapper as the view function.

    # correct: Flask registers the check_login wrapper
    @ui_bp.route('/images/series/<path:url>', methods=['GET'])
    @check_login
    def series_images(url): ...
"""
import pytest
from unittest.mock import patch
from flask import Flask

from bazarr.app.ui import ui_bp


@pytest.fixture
def app():
    application = Flask(__name__)
    application.register_blueprint(ui_bp)
    application.config['TESTING'] = True
    return application


def test_series_images_requires_basic_auth(app):
    """
    GET /images/series/* must return 401 when basic auth is configured and no
    credentials are supplied. Fails before fix: Flask dispatches directly to
    the original series_images function, bypassing check_login entirely.
    """
    with patch('bazarr.app.ui.settings') as mock_settings:
        mock_settings.auth.type = 'basic'
        with app.test_client() as client:
            response = client.get('/images/series/MediaCover/123/poster.jpg')
            assert response.status_code == 401


def test_movies_images_requires_basic_auth(app):
    """
    GET /images/movies/* must return 401 when basic auth is configured and no
    credentials are supplied.
    """
    with patch('bazarr.app.ui.settings') as mock_settings:
        mock_settings.auth.type = 'basic'
        with app.test_client() as client:
            response = client.get('/images/movies/MediaCover/456/poster.jpg')
            assert response.status_code == 401


def test_backup_download_requires_basic_auth(app):
    """
    GET /system/backup/download/* must return 401 when basic auth is configured
    and no credentials are supplied.
    """
    with patch('bazarr.app.ui.settings') as mock_settings:
        mock_settings.auth.type = 'basic'
        with app.test_client() as client:
            response = client.get('/system/backup/download/backup.zip')
            assert response.status_code == 401


def test_download_log_requires_basic_auth(app):
    """
    GET /bazarr.log must return 401 when basic auth is configured and no
    credentials are supplied.
    """
    with patch('bazarr.app.ui.settings') as mock_settings:
        mock_settings.auth.type = 'basic'
        with app.test_client() as client:
            response = client.get('/bazarr.log')
            assert response.status_code == 401
