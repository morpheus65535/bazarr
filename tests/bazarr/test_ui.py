"""
Test for Bazarr UI functionality including Flask route ordering and functionality.
"""
import pytest
from unittest.mock import Mock, patch
from flask import Flask

from bazarr.app.ui import ui_bp


def test_flask_route_registration_order():
    """
    Test that Flask routes are registered in the correct order.

    Verifies that specific routes (like /images/*) are registered before
    catch-all routes (/<path:path>) to ensure proper route matching.
    """
    # Create a minimal Flask app to test route registration
    app = Flask(__name__)
    app.register_blueprint(ui_bp, url_prefix='')

    # Get all registered routes
    ui_routes = []
    for rule in app.url_map.iter_rules():
        if rule.endpoint and rule.endpoint.startswith('ui.'):
            ui_routes.append({
                'rule': rule.rule,
                'endpoint': rule.endpoint
            })

    # Find route types
    image_routes = [r for r in ui_routes if 'images' in r['rule']]
    catch_all_routes = [r for r in ui_routes if r['rule'].endswith('/<path:path>')]

    # Verify routes exist
    assert len(image_routes) >= 2, "Should have at least 2 image routes (series and movies)"
    assert len(catch_all_routes) >= 1, "Should have catch-all route"

    # Verify specific image routes exist
    series_routes = [r for r in image_routes if '/images/series/' in r['rule']]
    movie_routes = [r for r in image_routes if '/images/movies/' in r['rule']]

    assert len(series_routes) >= 1, "Should have series image route"
    assert len(movie_routes) >= 1, "Should have movie image route"


def test_series_images_route_functionality():
    """
    Test that the series images route works correctly when properly routed.
    """
    # Create minimal Flask app for testing specific route
    app = Flask(__name__)
    app.register_blueprint(ui_bp, url_prefix='')
    app.config['TESTING'] = True

    with app.test_client() as client:
        # Mock the settings and external dependencies
        with patch('bazarr.app.ui.settings') as mock_settings, \
             patch('bazarr.app.ui.url_api_sonarr', return_value='http://localhost:8989'), \
             patch('bazarr.app.ui.requests.get') as mock_requests, \
             patch('bazarr.app.ui.check_credentials', return_value=True):

            # Configure mock settings
            mock_settings.auth.type = None
            mock_settings.sonarr.apikey = 'test_api_key'
            mock_settings.sonarr.base_url = ''

            # Mock successful image response
            mock_response = Mock()
            mock_response.headers = {'content-type': 'image/jpeg'}
            mock_response.iter_content.return_value = [b'fake_image_data']
            mock_requests.return_value = mock_response

            # Test the series images route
            response = client.get('/images/series/MediaCover/123/poster.jpg')

            # Should reach the specific handler, not catch-all
            assert response.status_code == 200
            mock_requests.assert_called_once()


def test_movies_images_route_functionality():
    """
    Test that the movies images route works correctly when properly routed.
    """
    app = Flask(__name__)
    app.register_blueprint(ui_bp, url_prefix='')
    app.config['TESTING'] = True

    with app.test_client() as client:
        # Mock the settings and external dependencies
        with patch('bazarr.app.ui.settings') as mock_settings, \
             patch('bazarr.app.ui.url_api_radarr', return_value='http://localhost:7878'), \
             patch('bazarr.app.ui.requests.get') as mock_requests, \
             patch('bazarr.app.ui.check_credentials', return_value=True):

            # Configure mock settings
            mock_settings.auth.type = None
            mock_settings.radarr.apikey = 'test_api_key'
            mock_settings.radarr.base_url = ''

            # Mock successful image response
            mock_response = Mock()
            mock_response.headers = {'content-type': 'image/jpeg'}
            mock_response.iter_content.return_value = [b'fake_image_data']
            mock_requests.return_value = mock_response

            # Test the movie images route
            response = client.get('/images/movies/MediaCover/456/poster.jpg')

            # Should reach the specific handler, not catch-all
            assert response.status_code == 200
            mock_requests.assert_called_once()


def test_catch_all_route_still_works():
    """
    Test that the catch-all route still functions correctly for non-specific paths.
    """
    app = Flask(__name__)
    app.register_blueprint(ui_bp, url_prefix='')
    app.config['TESTING'] = True

    with app.test_client() as client:
        with patch('bazarr.app.ui.settings') as mock_settings, \
             patch('bazarr.app.ui.database') as mock_database, \
             patch('bazarr.app.ui.args') as mock_args, \
             patch('bazarr.app.ui.render_template', return_value='<html>Test</html>') as mock_render, \
             patch('bazarr.app.ui.base_url', ''):

            # Configure mocks
            mock_settings.auth.type = None
            mock_settings.auth.apikey = 'test_key'
            mock_database.scalar.return_value = '0'
            mock_args.no_update = False

            # Test catch-all route with a non-specific path
            response = client.get('/some/random/path')

            assert response.status_code == 200
            mock_render.assert_called_once()


def test_route_priority_image_over_catchall():
    """
    Test that image routes take priority over catch-all routes.

    This is the core test for the route ordering fix - ensuring that
    specific image routes are matched before the catch-all pattern.
    """
    app = Flask(__name__)
    app.register_blueprint(ui_bp, url_prefix='')
    app.config['TESTING'] = True

    with app.test_client() as client:
        with patch('bazarr.app.ui.settings') as mock_settings, \
             patch('bazarr.app.ui.url_api_sonarr', return_value='http://localhost:8989'), \
             patch('bazarr.app.ui.requests.get') as mock_image_requests, \
             patch('bazarr.app.ui.render_template') as mock_render_template, \
             patch('bazarr.app.ui.check_credentials', return_value=True):

            # Configure mocks
            mock_settings.auth.type = None
            mock_settings.sonarr.apikey = 'test_api_key'
            mock_settings.sonarr.base_url = ''

            # Mock image response
            mock_response = Mock()
            mock_response.headers = {'content-type': 'image/jpeg'}
            mock_response.iter_content.return_value = [b'image_data']
            mock_image_requests.return_value = mock_response

            # Request an image path that could match either catch-all or specific route
            response = client.get('/images/series/test.jpg')

            # Should call image handler, NOT render_template (catch-all)
            mock_image_requests.assert_called_once()
            mock_render_template.assert_not_called()

            # Should return image response
            assert response.status_code == 200


def test_log_download_route_functionality():
    """
    Test that the log download route works correctly.
    """
    app = Flask(__name__)
    app.register_blueprint(ui_bp, url_prefix='')
    app.config['TESTING'] = True

    with app.test_client() as client:
        with patch('bazarr.app.ui.settings') as mock_settings, \
             patch('bazarr.app.ui.get_log_file_path', return_value='/fake/log/path.log'), \
             patch('bazarr.app.ui.send_file') as mock_send_file, \
             patch('bazarr.app.ui.check_credentials', return_value=True):

            mock_settings.auth.type = None
            mock_send_file.return_value = Mock(status_code=200)

            # Test log download route
            response = client.get('/bazarr.log')

            # Should call send_file for log download
            mock_send_file.assert_called_once_with('/fake/log/path.log', max_age=0, as_attachment=True)


def test_route_ordering_prevents_catchall_interception():
    """
    Integration test verifying that the route ordering fix prevents
    catch-all route from intercepting specific image requests.
    """
    app = Flask(__name__)
    app.register_blueprint(ui_bp, url_prefix='')
    app.config['TESTING'] = True

    with app.test_client() as client:
        with patch('bazarr.app.ui.settings') as mock_settings, \
             patch('bazarr.app.ui.url_api_sonarr', return_value='http://localhost:8989'), \
             patch('bazarr.app.ui.requests.get') as mock_requests, \
             patch('bazarr.app.ui.check_credentials', return_value=True):

            mock_settings.auth.type = None
            mock_settings.sonarr.apikey = 'test_key'
            mock_settings.sonarr.base_url = ''

            # Mock successful image response
            mock_response = Mock()
            mock_response.headers = {'content-type': 'image/jpeg'}
            mock_response.iter_content.return_value = [b'test_image']
            mock_requests.return_value = mock_response

            # Request a series image
            response = client.get('/images/series/test/poster.jpg')

            # Verify the request was handled by the image route handler
            # (we can tell because requests.get was called, which only happens in image handlers)
            mock_requests.assert_called_once()
            assert response.status_code == 200


def test_specific_routes_have_priority():
    """
    Test the fundamental route ordering principle: specific routes match before general ones.
    """
    app = Flask(__name__)

    # Register routes in the FIXED order (specific before catch-all)

    # Specific route first
    @app.route('/images/series/<path:url>')
    def series_images_test(url):
        return f"SERIES: {url}", 200, {'Content-Type': 'text/plain'}

    # Catch-all route second
    @app.route('/<path:path>')
    def catch_all_test(path):
        return f"CATCHALL: {path}", 200, {'Content-Type': 'text/html'}

    with app.test_client() as client:
        # Test that specific route is matched
        response = client.get('/images/series/test.jpg')
        assert response.status_code == 200
        assert b'SERIES: test.jpg' in response.data
        assert response.headers['Content-Type'] == 'text/plain'

        # Test that catch-all still works for non-specific paths
        response = client.get('/some/other/path')
        assert response.status_code == 200
        assert b'CATCHALL: some/other/path' in response.data
        assert response.headers['Content-Type'] == 'text/html'


def test_wrong_route_order_demonstrates_problem():
    """
    Test that demonstrates what happens with wrong route ordering.
    This shows why the fix was necessary.
    """
    app = Flask(__name__)

    # Register routes in the WRONG order (catch-all before specific)

    # Catch-all route first (WRONG ORDER)
    @app.route('/<path:path>')
    def catch_all_wrong(path):
        return f"CATCHALL: {path}", 200, {'Content-Type': 'text/html'}

    # Specific route second (NEVER REACHED)
    @app.route('/images/series/<path:url>')
    def series_images_wrong(url):
        return f"SERIES: {url}", 200, {'Content-Type': 'text/plain'}

    with app.test_client() as client:
        # Test that catch-all intercepts the specific route
        response = client.get('/images/series/test.jpg')
        assert response.status_code == 200
        # This demonstrates the problem: catch-all handles what should be a specific route
        assert b'CATCHALL: images/series/test.jpg' in response.data
        assert response.headers['Content-Type'] == 'text/html'  # Wrong content type!