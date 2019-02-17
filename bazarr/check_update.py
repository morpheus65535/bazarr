# coding=utf-8

import os
import platform
import re
import subprocess
import tarfile
import logging
import requests
import sqlite3
import json

from get_args import args
from config import settings, bazarr_url


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


def run_git(args):
    git_locations = ['git']
    
    if platform.system().lower() == 'darwin':
        git_locations.append('/usr/local/git/bin/git')
    
    output = err = None
    
    for cur_git in git_locations:
        cmd = cur_git + ' ' + args
        
        try:
            logging.debug('Trying to execute: "' + cmd + '"')
            p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
            output, err = p.communicate()
            output = output.strip()
            
            logging.debug('Git output: ' + output)
        except OSError:
            logging.debug('Command failed: %s', cmd)
            continue
        
        if 'not found' in output or "not recognized as an internal or external command" in output:
            logging.debug('Unable to find git with command ' + cmd)
            output = None
        elif 'fatal:' in output or err:
            logging.error('Git returned bad info. Are you sure this is a git installation?')
            output = None
        elif output:
            break
    
    return output, err


def check_updates():
    commits_behind = 0
    current_version = get_version()
    
    # Get the latest version available from github
    logging.info('Retrieving latest version information from GitHub')
    url = 'https://api.github.com/repos/morpheus65535/bazarr/commits/%s' % settings.general.branch
    version = request_json(url, timeout=20, validator=lambda x: type(x) == dict)
    
    if version is None:
        logging.warn('Could not get the latest version from GitHub. Are you running a local development version?')
        return current_version
    
    latest_version = version['sha']
    logging.debug("Latest version is %s", latest_version)
    
    # See how many commits behind we are
    if not current_version:
        logging.info('You are running an unknown version of Bazarr. Run the updater to identify your version')
        return latest_version
    
    if latest_version == current_version:
        logging.info('Bazarr is up to date')
        return latest_version
    
    logging.info('Comparing currently installed version with latest GitHub version')
    url = 'https://api.github.com/repos/morpheus65535/bazarr/compare/%s...%s' % (latest_version,
                                                                                 current_version)
    commits = request_json(url, timeout=20, whitelist_status_code=404, validator=lambda x: type(x) == dict)
    
    if commits is None:
        logging.warn('Could not get commits behind from GitHub.')
        return latest_version
    
    try:
        commits_behind = int(commits['behind_by'])
        logging.debug("In total, %d commits behind", commits_behind)
    except KeyError:
        logging.info('Cannot compare versions. Are you running a local development version?')
        commits_behind = 0
    
    if commits_behind > 0:
        logging.info('New version is available. You are %s commits behind' % commits_behind)
        update()
    
    url = 'https://api.github.com/repos/morpheus65535/bazarr/releases'
    releases = request_json(url, timeout=20, whitelist_status_code=404, validator=lambda x: type(x) == list)
    
    if releases is None:
        logging.warn('Could not get releases from GitHub.')
        return latest_version
    else:
        release = releases[0]
    latest_release = release['tag_name']
    
    if ('v' + current_version) != latest_release and args.release_update:
        update()
    
    elif commits_behind == 0:
        logging.info('Bazarr is up to date')
    
    return latest_version


def get_version():
    if os.path.isdir(os.path.join(os.path.dirname(__file__), '..', '.git')):
        
        output, err = run_git('rev-parse HEAD')
        
        if not output:
            logging.error('Could not find latest installed version.')
            cur_commit_hash = None
        else:
            cur_commit_hash = str(output)
        
        if not re.match('^[a-z0-9]+$', cur_commit_hash):
            logging.error('Output does not look like a hash, not using it.')
            cur_commit_hash = None
        
        return cur_commit_hash
    
    else:
        return os.environ["BAZARR_VERSION"]


def update():
    if not args.release_update:
        output, err = run_git('pull ' + 'origin' + ' ' + settings.general.branch)
        
        if not output:
            logging.error('Unable to download latest version')
            return
        
        for line in output.split('\n'):
            
            if 'Already up-to-date.' in line:
                logging.info('No update available, not updating')
                logging.info('Output: ' + str(output))
            elif line.endswith(('Aborting', 'Aborting.')):
                logging.error('Unable to update from git: ' + line)
                logging.info('Output: ' + str(output))
        updated()
    else:
        tar_download_url = 'https://github.com/morpheus65535/bazarr/tarball/{}'.format(settings.general.branch)
        update_dir = os.path.join(os.path.dirname(__file__), '..', 'update')
        
        logging.info('Downloading update from: ' + tar_download_url)
        data = request_content(tar_download_url)
        
        if not data:
            logging.error("Unable to retrieve new version from '%s', can't update", tar_download_url)
            return
        
        download_name = settings.general.branch + '-github'
        tar_download_path = os.path.join(os.path.dirname(__file__), '..', download_name)
        
        # Save tar to disk
        with open(tar_download_path, 'wb') as f:
            f.write(data)
        
        # Extract the tar to update folder
        logging.info('Extracting file: ' + tar_download_path)
        tar = tarfile.open(tar_download_path)
        tar.extractall(update_dir)
        tar.close()
        
        # Delete the tar.gz
        logging.info('Deleting file: ' + tar_download_path)
        os.remove(tar_download_path)
        
        # Find update dir name
        update_dir_contents = [x for x in os.listdir(update_dir) if os.path.isdir(os.path.join(update_dir, x))]
        if len(update_dir_contents) != 1:
            logging.error("Invalid update data, update failed: " + str(update_dir_contents))
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
                "Requesting URL via %s method: %s", method.upper(), url)
            response = request_method(url, **kwargs)
        
        # If status code != OK, then raise exception, except if the status code
        # is white listed.
        if whitelist_status_code and auto_raise:
            if response.status_code not in whitelist_status_code:
                try:
                    response.raise_for_status()
                except:
                    logging.debug(
                        "Response status code %d is not white "
                        "listed, raised exception", response.status_code)
                    raise
        elif auto_raise:
            response.raise_for_status()
        
        return response
    except requests.exceptions.SSLError as e:
        if kwargs["verify"]:
            logging.error(
                "Unable to connect to remote host because of a SSL error. "
                "It is likely that your system cannot verify the validity"
                "of the certificate. The remote certificate is either "
                "self-signed, or the remote server uses SNI. See the wiki for "
                "more information on this topic.")
        else:
            logging.error(
                "SSL error raised during connection, with certificate "
                "verification turned off: %s", e)
    except requests.ConnectionError:
        logging.error(
            "Unable to connect to remote host. Check if the remote "
            "host is up and running.")
    except requests.Timeout:
        logging.error(
            "Request timed out. The remote host did not respond timely.")
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
                "Request raise HTTP error with status code %d (%s).",
                e.response.status_code, cause)
            
            # Debug response
            # if bazarr.DEBUG:
            #     server_message(e.response)
        else:
            logging.error("Request raised HTTP error.")
    except requests.RequestException as e:
        logging.error("Request raised exception: %s", e)


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
                logging.error("JSON validation result failed")
            else:
                return result
        except ValueError:
            logging.error("Response returned invalid JSON data")
            
            # Debug response
            # if bazarr.DEBUG:
            #     server_message(response)


def updated():
    conn = sqlite3.connect(os.path.join(args.config_dir, 'db', 'bazarr.db'), timeout=30)
    c = conn.cursor()
    c.execute("UPDATE system SET updated = 1")
    conn.commit()
    c.close()
    try:
        requests.get(bazarr_url + 'restart')
    except requests.ConnectionError:
        logging.info('BAZARR: Restart failed, please restart Bazarr manualy')
