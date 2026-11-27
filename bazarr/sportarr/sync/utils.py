# coding=utf-8

import requests
import logging

from app.config import settings
from constants import HEADERS
from sportarr.info import url_api_sportarr


def get_tags():
    apikey_sportarr = settings.sportarr.apikey
    tagsDict = []

    # Get tags data from Sportarr
    url_sportarr_api_tags = f"{url_api_sportarr()}tag?apikey={apikey_sportarr}"

    try:
        tagsDict = requests.get(url_sportarr_api_tags, timeout=int(settings.sportarr.http_timeout), verify=False,
                                headers=HEADERS)
    except requests.exceptions.ConnectionError:
        logging.exception("BAZARR Error trying to get tags from Sportarr. Connection Error.")
        return []
    except requests.exceptions.Timeout:
        logging.exception("BAZARR Error trying to get tags from Sportarr. Timeout Error.")
        return []
    except requests.exceptions.RequestException:
        logging.exception("BAZARR Error trying to get tags from Sportarr.")
        return []
    else:
        return tagsDict.json()


def get_event_from_sportarr_api(apikey_sportarr, event_id):
    """Read a single event.

    Returns None when Sportarr says the event does not exist. Raises
    requests.RequestException when Sportarr cannot answer, so the caller can
    retry the change later instead of losing it.
    """
    url_sportarr_api_event = f"{url_api_sportarr()}events/{event_id}?apikey={apikey_sportarr}"

    r = requests.get(url_sportarr_api_event, timeout=int(settings.sportarr.http_timeout), verify=False,
                     headers=HEADERS)
    if r.status_code == 404:
        return None
    r.raise_for_status()
    return r.json()


def get_league_from_sportarr_api(apikey_sportarr, league_id):
    """Read a single league.

    Returns None when Sportarr says the league does not exist. Raises
    requests.RequestException when Sportarr cannot answer.
    """
    url_sportarr_api_league = f"{url_api_sportarr()}leagues/{league_id}?apikey={apikey_sportarr}"

    r = requests.get(url_sportarr_api_league, timeout=int(settings.sportarr.http_timeout), verify=False,
                     headers=HEADERS)
    if r.status_code == 404:
        return None
    r.raise_for_status()
    return r.json()


def get_events_from_sportarr_api(apikey_sportarr, league_id):
    """Walk every page of a league's events.

    A season can run to a few thousand events, so this pages rather than
    asking for the lot. Returning None on any failure matters, because a
    partial walk read as a complete one looks like the league lost most of
    its events, and the caller would delete them.
    """
    events = []
    page = 1
    total_records = None

    while True:
        # showAll bypasses the league monitoring filters. Without it, an event
        # that a filter hides is missing from the list and looks removed.
        url_sportarr_api_events = (f"{url_api_sportarr()}leagues/{league_id}/events?"
                                   f"page={page}&pageSize=1000&showAll=true&apikey={apikey_sportarr}")

        try:
            r = requests.get(url_sportarr_api_events, timeout=int(settings.sportarr.http_timeout), verify=False,
                             headers=HEADERS)
            r.raise_for_status()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code:
                logging.exception(f"BAZARR Error trying to get events from Sportarr. HTTP error "
                                  f"{e.response.status_code}")
            return
        except requests.exceptions.ConnectionError:
            logging.exception("BAZARR Error trying to get events from Sportarr. Connection Error.")
            return
        except requests.exceptions.Timeout:
            logging.exception("BAZARR Error trying to get events from Sportarr. Timeout Error.")
            return
        except requests.exceptions.RequestException:
            logging.exception("BAZARR Error trying to get events from Sportarr.")
            return
        except Exception as e:
            logging.exception(f"Exception raised while getting events from Sportarr API: {e}")
            return

        try:
            result = r.json()
        except ValueError:
            logging.exception("BAZARR Error trying to get events from Sportarr. Invalid response.")
            return
        # A page without its records or its page count cannot prove the walk
        # is complete, so it counts as a failed read.
        records = result.get('records') if isinstance(result, dict) else None
        total_pages = result.get('totalPages') if isinstance(result, dict) else None
        if not isinstance(records, list) or type(total_pages) is not int:
            logging.debug(f'BAZARR Sportarr events sync returned an invalid payload for league {league_id}.')
            return
        events += records
        if type(result.get('totalRecords')) is int:
            total_records = result['totalRecords']

        if page >= total_pages:
            break
        page += 1

    if total_records is not None and len(events) != total_records:
        # The list changed during the walk, so it may be missing events.
        logging.debug(f'BAZARR Sportarr returned {len(events)} of {total_records} events for league {league_id}.')
        return

    return events


def get_leagues_from_sportarr_api(apikey_sportarr, sportarr_league_id=None):
    url_sportarr_api_leagues = (f"{url_api_sportarr()}leagues/{sportarr_league_id if sportarr_league_id else ''}?"
                                f"apikey={apikey_sportarr}")

    try:
        r = requests.get(url_sportarr_api_leagues, timeout=int(settings.sportarr.http_timeout), verify=False,
                         headers=HEADERS)
        r.raise_for_status()
    except requests.exceptions.HTTPError as e:
        if e.response.status_code:
            logging.exception(f"BAZARR Error trying to get leagues from Sportarr. HTTP error {e.response.status_code}")
        return
    except requests.exceptions.ConnectionError:
        logging.exception("BAZARR Error trying to get leagues from Sportarr. Connection Error.")
        return
    except requests.exceptions.Timeout:
        logging.exception("BAZARR Error trying to get leagues from Sportarr. Timeout Error.")
        return
    except requests.exceptions.RequestException:
        logging.exception("BAZARR Error trying to get leagues from Sportarr.")
        return
    except Exception as e:
        logging.exception(f"Exception raised while getting leagues from Sportarr API: {e}")
        return
    else:
        result = r.json()
        if isinstance(result, dict):
            return [result]
        return result
