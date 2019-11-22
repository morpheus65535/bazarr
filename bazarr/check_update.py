# coding=utf-8
import os
import logging
import json
import requests
import tarfile

from get_args import args
from config import settings
from queueconfig import notifications
from database import database

if not args.no_update and not args.release_update:
    import git

current_working_directory = os.path.dirname(os.path.dirname(__file__))


def gitconfig():
    g = git.Repo.init(current_working_directory)
    config_read = g.config_reader()
    config_write = g.config_writer()
    
    try:
        username = config_read.get_value("user", "name")
    except:
        logging.debug('BAZARR Settings git username')
        config_write.set_value("user", "name", "Bazarr")
    
    try:
        email = config_read.get_value("user", "email")
    except:
        logging.debug('BAZARR Settings git email')
        config_write.set_value("user", "email", "bazarr@fake.email")


def check_and_apply_update():
    check_releases()
    if not args.release_update:
        gitconfig()
        branch = settings.general.branch
        g = git.cmd.Git(current_working_directory)
        g.fetch('origin')
        result = g.diff('--shortstat', 'origin/' + branch)
        if len(result) == 0:
            notifications.write(msg='No new version of Bazarr available.', queue='check_update')
            logging.info('BAZARR No new version of Bazarr available.')
        else:
            g.reset('--hard', 'HEAD')
            g.checkout(branch)
            g.reset('--hard', 'origin/' + branch)
            g.pull()
            logging.info('BAZARR Updated to latest version. Restart required. ' + result)
            updated()
    else:
        url = 'https://api.github.com/repos/morpheus65535/bazarr/releases'
        releases = request_json(url, timeout=20, whitelist_status_code=404, validator=lambda x: type(x) == list)
        
        if releases is None:
            notifications.write(msg='Could not get releases from GitHub.',
                                queue='check_update', type='warning')
            logging.warn('BAZARR Could not get releases from GitHub.')
            return
        else:
            release = releases[0]
        latest_release = release['tag_name']
        
        if ('v' + os.environ["BAZARR_VERSION"]) != latest_release:
            update_from_source()
        else:
            notifications.write(msg='Bazarr is up to date', queue='check_update')
            logging.info('BAZARR is up to date')


def update_from_source():
    tar_download_url = 'https://github.com/morpheus65535/bazarr/tarball/{}'.format(settings.general.branch)
    update_dir = os.path.join(os.path.dirname(__file__), '..', 'update')
    
    logging.info('BAZARR Downloading update from: ' + tar_download_url)
    notifications.write(msg='Downloading update from: ' + tar_download_url, queue='check_update')
    data = request_content(tar_download_url)
    
    if not data:
        logging.error("BAZARR Unable to retrieve new version from '%s', can't update", tar_download_url)
        notifications.write(msg=("Unable to retrieve new version from '%s', can't update", tar_download_url),
                            type='error', queue='check_update')
        return
    
    download_name = settings.general.branch + '-github'
    tar_download_path = os.path.join(os.path.dirname(__file__), '..', download_name)
    
    # Save tar to disk
    with open(tar_download_path, 'wb') as f:
        f.write(data)
    
    # Extract the tar to update folder
    logging.info('BAZARR Extracting file: ' + tar_download_path)
    notifications.write(msg='Extracting file: ' + tar_download_path, queue='check_update')
    tar = tarfile.open(tar_download_path)
    tar.extractall(update_dir)
    tar.close()
    
    # Delete the tar.gz
    logging.info('BAZARR Deleting file: ' + tar_download_path)
    notifications.write(msg='Deleting file: ' + tar_download_path, queue='check_update')
    os.remove(tar_download_path)
    
    # Find update dir name
    update_dir_contents = [x for x in os.listdir(update_dir) if os.path.isdir(os.path.join(update_dir, x))]
    if len(update_dir_contents) != 1:
        logging.error("BAZARR Invalid update data, update failed: " + str(update_dir_contents))
        notifications.write(msg="BAZARR Invalid update data, update failed: " + str(update_dir_contents),
                            type='error', queue='check_update')
        return
    
    content_dir = os.path.join(update_dir, update_dir_contents[0])
    
    # walk temp folder and move files to main folder
    for dirname, dirnames, filenames in os.walk(content_dir):
        dirname = dirname[len(content_dir) + 1:]
        for curfile in filenames:
            old_path = os.path.join(content_dir, dirname, curfile)
            new_path = os.path.join(os.path.dirname(__file__), '..', dirname, curfile)
            
            if os.path.isfile(new_path):
                os.remove(new_path)
            os.renames(old_path, new_path)
    updated()


def check_releases():
    releases = []
    url_releases = 'https://api.github.com/repos/morpheus65535/Bazarr/releases'
    try:
        r = requests.get(url_releases, timeout=15)
        r.raise_for_status()
    except requests.exceptions.HTTPError as errh:
        logging.exception("Error trying to get releases from Github. Http error.")
    except requests.exceptions.ConnectionError as errc:
        logging.exception("Error trying to get releases from Github. Connection Error.")
    except requests.exceptions.Timeout as errt:
        logging.exception("Error trying to get releases from Github. Timeout Error.")
    except requests.exceptions.RequestException as err:
        logging.exception("Error trying to get releases from Github.")
    else:
        for release in r.json():
            releases.append([release['name'], release['body']])
        with open(os.path.join(args.config_dir, 'config', 'releases.txt'), 'w') as f:
            json.dump(releases, f)


class FakeLock(object):
    """
    If no locking or request throttling is needed, use this
    """
    
    def __enter__(self):
        """
        Do nothing on enter
        """
        pass
    
    def __exit__(self, type, value, traceback):
        """
        Do nothing on exit
        """
        pass


fake_lock = FakeLock()


def request_content(url, **kwargs):
    """
    Wrapper for `request_response', which will return the raw content.
    """
    
    response = request_response(url, **kwargs)
    
    if response is not None:
        return response.content


def request_response(url, method="get", auto_raise=True,
                     whitelist_status_code=None, lock=fake_lock, **kwargs):
    """
    Convenient wrapper for `requests.get', which will capture the exceptions
    and log them. On success, the Response object is returned. In case of a
    exception, None is returned.

    Additionally, there is support for rate limiting. To use this feature,
    supply a tuple of (lock, request_limit). The lock is used to make sure no
    other request with the same lock is executed. The request limit is the
    minimal time between two requests (and so 1/request_limit is the number of
    requests per seconds).
    """
    
    # Convert whitelist_status_code to a list if needed
    if whitelist_status_code and type(whitelist_status_code) != list:
        whitelist_status_code = [whitelist_status_code]
    
    # Disable verification of SSL certificates if requested. Note: this could
    # pose a security issue!
    kwargs["verify"] = True
    
    # Map method to the request.XXX method. This is a simple hack, but it
    # allows requests to apply more magic per method. See lib/requests/api.py.
    request_method = getattr(requests, method.lower())
    
    try:
        # Request URL and wait for response
        with lock:
            logging.debug(
                "BAZARR Requesting URL via %s method: %s", method.upper(), url)
            response = request_method(url, **kwargs)
        
        # If status code != OK, then raise exception, except if the status code
        # is white listed.
        if whitelist_status_code and auto_raise:
            if response.status_code not in whitelist_status_code:
                try:
                    response.raise_for_status()
                except:
                    logging.debug(
                        "BAZARR Response status code %d is not white "
                        "listed, raised exception", response.status_code)
                    raise
        elif auto_raise:
            response.raise_for_status()
        
        return response
    except requests.exceptions.SSLError as e:
        if kwargs["verify"]:
            logging.error(
                "BAZARR Unable to connect to remote host because of a SSL error. "
                "It is likely that your system cannot verify the validity"
                "of the certificate. The remote certificate is either "
                "self-signed, or the remote server uses SNI. See the wiki for "
                "more information on this topic.")
        else:
            logging.error(
                "BAZARR SSL error raised during connection, with certificate "
                "verification turned off: %s", e)
    except requests.ConnectionError:
        logging.error(
            "BAZARR Unable to connect to remote host. Check if the remote "
            "host is up and running.")
    except requests.Timeout:
        logging.error(
            "BAZARR Request timed out. The remote host did not respond timely.")
    except requests.HTTPError as e:
        if e.response is not None:
            if e.response.status_code >= 500:
                cause = "remote server error"
            elif e.response.status_code >= 400:
                cause = "local client error"
            else:
                # I don't think we will end up here, but for completeness
                cause = "unknown"
            
            logging.error(
                "BAZARR Request raise HTTP error with status code %d (%s).",
                e.response.status_code, cause)
        else:
            logging.error("BAZARR Request raised HTTP error.")
    except requests.RequestException as e:
        logging.error("BAZARR Request raised exception: %s", e)


def request_json(url, **kwargs):
    """
    Wrapper for `request_response', which will decode the response as JSON
    object and return the result, if no exceptions are raised.

    As an option, a validator callback can be given, which should return True
    if the result is valid.
    """
    
    validator = kwargs.pop("validator", None)
    response = request_response(url, **kwargs)
    
    if response is not None:
        try:
            result = response.json()
            
            if validator and not validator(result):
                logging.error("BAZARR JSON validation result failed")
            else:
                return result
        except ValueError:
            logging.error("BAZARR Response returned invalid JSON data")


def updated(restart=True):
    if settings.general.getboolean('update_restart') and restart:
        try:
            from main import restart
            restart()
        except:
            logging.info('BAZARR Restart failed, please restart Bazarr manualy')
            updated(restart=False)
    else:
        database.execute("UPDATE system SET updated='1'")
