from __future__ import absolute_import
import io
import logging
import os
import re
import zipfile
from requests import Session
from bs4 import BeautifulSoup
from subliminal_patch.subtitle import Subtitle
from subliminal_patch.providers import Provider
from subliminal.subtitle import fix_line_ending
from subliminal.utils import sanitize
from subliminal.video import Episode, Movie
from subzero.language import Language
from guessit import guessit

logger = logging.getLogger(__name__)


class AnimesubinfoSubtitle(Subtitle):
    """AnimeSub.info Subtitle."""
    provider_name = 'animesubinfo'

    def __init__(self, language, video, subtitle_id, title_org, title_eng, title_alt,
                 author, format_type, size, download_hash, download_count=0, description=''):
        super(AnimesubinfoSubtitle, self).__init__(language)
        self.video = video
        self.subtitle_id = subtitle_id
        self.title_org = title_org
        self.title_eng = title_eng
        self.title_alt = title_alt
        self.author = author
        self.format_type = format_type
        self.size = size
        self.download_hash = download_hash
        self.download_count = download_count
        self.description = description
        self.uploader = author  # Store author as uploader for Bazarr UI
        self.page_link = f'http://animesub.info/'
        self.release_info = f'{title_org} - {title_eng}'

        # Parse episode and season from titles
        self.season = None
        self.episode = None
        self._parse_episode_info()

        # Parse release groups from description (Synchro field)
        self.release_groups = []
        self._parse_release_groups()

    @property
    def id(self):
        return self.subtitle_id

    def _parse_episode_info(self):
        """Parse episode and season number from subtitle titles."""
        # Pattern to match episode numbers: ep01, ep1, episode 01, etc.
        episode_pattern = r'(?:ep|episode)\s*(\d+)'
        # Pattern to match season: Season 2, S02, 2nd Season, etc.
        season_pattern = r'(?:Season|S)\s*(\d+)|(\d+)(?:nd|rd|th)\s+Season'

        # Try to extract episode from all title variants
        for title in [self.title_org, self.title_eng, self.title_alt]:
            if title and self.episode is None:
                match = re.search(episode_pattern, title, re.IGNORECASE)
                if match:
                    self.episode = int(match.group(1))
                    logger.debug(f'Parsed episode {self.episode} from title: {title}')

            if title and self.season is None:
                match = re.search(season_pattern, title, re.IGNORECASE)
                if match:
                    # Can be in group 1 (Season X, SX) or group 2 (Xnd Season)
                    self.season = int(match.group(1) or match.group(2))
                    logger.debug(f'Parsed season {self.season} from title: {title}')

    def _parse_release_groups(self):
        """Parse release groups from description (Synchro field)."""
        if not self.description:
            return

        # Look for "Synchro:" line in description
        # Examples:
        # "Synchro: [SubsPlease]"
        # "Synchro: SubsPlease, Erai-raws, VARYG (CR)"
        # "Synchro do [Erai-raws]"
        synchro_pattern = r'Synchro[:\s]+([^\n<]+)'
        match = re.search(synchro_pattern, self.description, re.IGNORECASE)

        if match:
            synchro_text = match.group(1).strip()
            logger.debug(f'Found Synchro line: {synchro_text}')

            # Extract release groups from the synchro text
            # Remove common words and extract group names
            # Patterns: [GroupName], GroupName, GroupName (source)
            groups = []

            # Pattern 1: [GroupName]
            bracket_groups = re.findall(r'\[([^\]]+)\]', synchro_text)
            groups.extend(bracket_groups)

            # Pattern 2: Clean group names separated by commas
            # Remove brackets first, then split by comma
            cleaned_text = re.sub(r'\[([^\]]+)\]', r'\1', synchro_text)
            # Remove text in parentheses like (CR)
            cleaned_text = re.sub(r'\([^)]+\)', '', cleaned_text)
            # Split by comma and clean
            parts = [p.strip() for p in cleaned_text.split(',')]
            groups.extend([p for p in parts if p and len(p) > 2])

            # Clean and deduplicate
            self.release_groups = list(set(g.strip() for g in groups if g.strip()))
            logger.debug(f'Parsed release groups: {self.release_groups}')

    def get_matches(self, video):
        matches = set()
        logger.debug(f'Matching subtitle {self.subtitle_id} against video: {video}')

        # Sanitize titles for comparison
        video_title = sanitize(video.title if isinstance(video, Movie) else video.series)

        # Check against all three title variants
        if video_title:
            if sanitize(self.title_org) and video_title in sanitize(self.title_org):
                matches.add('title')
            elif sanitize(self.title_eng) and video_title in sanitize(self.title_eng):
                matches.add('title')
            elif sanitize(self.title_alt) and video_title in sanitize(self.title_alt):
                matches.add('title')

        # For episodes, check series match
        if isinstance(video, Episode):
            if video.series:
                series_sanitized = sanitize(video.series)
                if series_sanitized in (sanitize(self.title_org) or ''):
                    matches.add('series')
                elif series_sanitized in (sanitize(self.title_eng) or ''):
                    matches.add('series')
                elif series_sanitized in (sanitize(self.title_alt) or ''):
                    matches.add('series')

            # Season match
            if video.season and self.season == video.season:
                matches.add('season')
            elif video.season == 1 and self.season is None:
                # If video is season 1 and subtitle doesn't specify season,
                # assume it's season 1 (common for anime)
                matches.add('season')

            # Episode match
            if video.episode and self.episode == video.episode:
                matches.add('episode')

            # Release group match
            if self.release_groups and hasattr(video, 'release_group') and video.release_group:
                video_group = video.release_group.lower()
                for subtitle_group in self.release_groups:
                    if video_group == subtitle_group.lower():
                        matches.add('release_group')
                        logger.debug(f'Release group match: {video_group} == {subtitle_group}')
                        break

        # Year matching for movies
        if isinstance(video, Movie) and video.year:
            # Try to extract year from titles
            year_pattern = r'\b(19|20)\d{2}\b'
            for title in [self.title_org, self.title_eng, self.title_alt]:
                if title:
                    year_match = re.search(year_pattern, title)
                    if year_match and int(year_match.group(0)) == video.year:
                        matches.add('year')
                        break

        # Video type match
        video_type = 'movie' if isinstance(video, Movie) else 'episode'
        matches.add(video_type)

        # Format preference - Advanced SSA/ASS is better quality
        if self.format_type and 'Advanced SSA' in self.format_type:
            matches.add('audio_codec')  # Repurpose for format priority

        logger.debug(f'Subtitle {self.subtitle_id} matches: {matches}')
        return matches


class AnimesubinfoProvider(Provider):
    """AnimeSub.info Provider."""
    languages = {Language('pol')}
    video_types = (Episode, Movie)

    base_url = 'http://animesub.info'
    search_url = 'http://animesub.info/szukaj.php'
    download_url = 'http://animesub.info/sciagnij.php'

    def __init__(self):
        self.session = None

    def initialize(self):
        self.session = Session()
        self.session.headers['User-Agent'] = os.environ.get("SZ_USER_AGENT", "Sub-Zero/2")
        # Set encoding to handle ISO-8859-2 (Polish) properly
        self.session.headers['Accept-Charset'] = 'ISO-8859-2,utf-8;q=0.7,*;q=0.3'

    def terminate(self):
        if self.session:
            self.session.close()

    def _search_titles(self, title, title_type='org'):
        """
        Search for subtitles by title.

        Args:
            title: The title to search for
            title_type: Type of title - 'org' (original), 'en' (English), 'pl' (Polish alternative)
        """
        params = {
            'szukane': title,
            'pTitle': title_type,
            'pSortuj': 'pobrn'  # Sort by download count (most popular first)
        }

        logger.info(f'Searching AnimeSub.info for: {title} (type: {title_type})')

        try:
            response = self.session.get(self.search_url, params=params, timeout=10)
            response.raise_for_status()

            # Handle Polish encoding
            response.encoding = 'ISO-8859-2'

            return response.text
        except Exception as e:
            logger.error(f'Error searching AnimeSub.info: {e}')
            return None

    def _parse_search_results(self, html_content, video):
        """Parse search results HTML and extract subtitle information."""
        if not html_content:
            return []

        soup = BeautifulSoup(html_content, 'html.parser')
        subtitles = []

        # Find all subtitle entries
        # Each subtitle is in a table with class "Napisy"
        subtitle_tables = soup.find_all('table', class_='Napisy', style=lambda value: value and 'text-align:center' in value)

        for table in subtitle_tables:
            try:
                rows = table.find_all('tr', class_='KNap')
                if len(rows) < 3:
                    continue

                # Extract subtitle information from the three rows
                # Row 1: Original title, date, placeholder, format
                row1 = rows[0].find_all('td')
                title_org = row1[0].get_text(strip=True) if len(row1) > 0 else ''
                date_added = row1[1].get_text(strip=True) if len(row1) > 1 else ''
                format_type = row1[3].get_text(strip=True) if len(row1) > 3 else ''

                # Row 2: English title, author, quality, size
                row2 = rows[1].find_all('td')
                title_eng = row2[0].get_text(strip=True) if len(row2) > 0 else ''

                # Parse author - try link first, then fallback to text content
                author = ''
                if len(row2) > 1:
                    author_cell = row2[1]
                    author_link = author_cell.find('a')
                    if author_link:
                        author = author_link.get_text(strip=True)
                    else:
                        author = author_cell.get_text(strip=True)
                    # Remove leading ~ if present
                    author = author.lstrip('~')

                # Parse size from the last cell of row2 (typically row2[4])
                # Note: Row2 has 5 cells due to quality bar taking 2 cells
                size = row2[-1].get_text(strip=True) if len(row2) > 0 else ''

                # Row 3: Alternative title, comments, mod, downloads
                row3 = rows[2].find_all('td')
                title_alt = row3[0].get_text(strip=True) if len(row3) > 0 else ''

                # Parse download count (format: "308 razy" or "1234 razy")
                download_count = 0
                if len(row3) > 3:
                    download_text = row3[3].get_text(strip=True)
                    try:
                        # Extract just the number from "308 razy"
                        download_count = int(download_text.split()[0])
                    except (ValueError, AttributeError, IndexError):
                        logger.debug(f'Could not parse download count from: {download_text}')
                        pass

                # Find the download form in the last row
                download_row = table.find('tr', class_='KKom')
                if not download_row:
                    continue

                form = download_row.find('form', method='POST')
                if not form:
                    continue

                # Extract subtitle ID and hash from hidden inputs
                subtitle_id_input = form.find('input', {'name': 'id'})
                hash_input = form.find('input', {'name': 'sh'})

                if not subtitle_id_input or not hash_input:
                    continue

                subtitle_id = subtitle_id_input.get('value', '')
                download_hash = hash_input.get('value', '')

                # Extract description/comment (contains Synchro info)
                description = ''
                description_cell = download_row.find('td', class_='KNap', align='left')
                if description_cell:
                    description = description_cell.get_text(strip=False)

                logger.debug(f'Found subtitle: ID={subtitle_id}, Org={title_org}, Eng={title_eng}, Alt={title_alt}, Author={author}, Downloads={download_count}')

                # Create subtitle object
                subtitle = AnimesubinfoSubtitle(
                    language=Language('pol'),
                    video=video,
                    subtitle_id=subtitle_id,
                    title_org=title_org,
                    title_eng=title_eng,
                    title_alt=title_alt,
                    author=author,
                    format_type=format_type,
                    size=size,
                    download_hash=download_hash,
                    download_count=download_count,
                    description=description
                )

                subtitles.append(subtitle)

            except Exception as e:
                logger.warning(f'Error parsing subtitle entry: {e}')
                continue

        logger.info(f'Found {len(subtitles)} subtitles')
        return subtitles

    def list_subtitles(self, video, languages):
        """List all available subtitles for the video."""
        if Language('pol') not in languages:
            logger.debug('Polish not in requested languages')
            return []

        # Determine the search title
        if isinstance(video, Episode):
            search_title = video.series
            # For episodes, use pattern like "Kimetsu no Yaiba ep01"
            if video.episode:
                search_title_with_ep = f'{search_title} ep{video.episode:02d}'
            else:
                search_title_with_ep = None
        else:
            search_title = video.title
            search_title_with_ep = None

        all_subtitles = []

        # Try multiple search strategies
        search_strategies = []

        # Strategy 1: For episodes, prioritize search with "epXX" pattern
        if isinstance(video, Episode) and search_title_with_ep:
            # Try original title first (Japanese), then English, then Polish
            search_strategies.append(('org', search_title_with_ep))
            search_strategies.append(('en', search_title_with_ep))
            search_strategies.append(('pl', search_title_with_ep))

        # Strategy 2: Search without episode number (for series packs or general search)
        if not isinstance(video, Episode) or not search_title_with_ep:
            search_strategies.append(('org', search_title))
            search_strategies.append(('en', search_title))
            search_strategies.append(('pl', search_title))

        # Strategy 3: Try alternative titles if available
        if isinstance(video, Episode) and video.alternative_series:
            for alt_series in video.alternative_series[:2]:  # Limit to first 2 alternatives
                if video.episode:
                    search_strategies.append(('en', f'{alt_series} ep{video.episode:02d}'))
                search_strategies.append(('en', alt_series))
        elif isinstance(video, Movie) and video.alternative_titles:
            for alt_title in video.alternative_titles[:2]:  # Limit to first 2 alternatives
                search_strategies.append(('en', alt_title))
                search_strategies.append(('org', alt_title))

        # Execute searches
        seen_ids = set()
        for title_type, title in search_strategies:
            html = self._search_titles(title, title_type)
            if html:
                results = self._parse_search_results(html, video)
                for sub in results:
                    if sub.subtitle_id not in seen_ids:
                        all_subtitles.append(sub)
                        seen_ids.add(sub.subtitle_id)

                # If we found results with episode number, we can stop searching
                if results and search_title_with_ep and search_title_with_ep in title:
                    logger.info(f'Found {len(results)} results with episode pattern, stopping search')
                    break

        logger.info(f'Returning {len(all_subtitles)} subtitles')
        return all_subtitles

    def download_subtitle(self, subtitle):
        """Download the subtitle content."""
        try:
            data = {
                'id': subtitle.subtitle_id,
                'sh': subtitle.download_hash,
                'single_file': 'Pobierz napisy'  # Submit button value
            }

            logger.info(f'Downloading subtitle ID: {subtitle.subtitle_id}')

            response = self.session.post(self.download_url, data=data, timeout=10)
            response.raise_for_status()

            # Check if we got actual subtitle content
            if len(response.content) < 50:
                logger.error('Downloaded file is too small, possibly an error')
                return

            # Check if it's a ZIP file
            if zipfile.is_zipfile(io.BytesIO(response.content)):
                logger.info(f'Downloaded file is a ZIP archive, extracting...')
                with zipfile.ZipFile(io.BytesIO(response.content)) as zf:
                    # Find subtitle files in the archive
                    subtitle_files = [f for f in zf.namelist()
                                    if f.lower().endswith(('.srt', '.ass', '.ssa', '.sub'))]

                    if not subtitle_files:
                        logger.error('No subtitle file found in ZIP archive')
                        return

                    # Use the first subtitle file found
                    # TODO: Could be improved to select best matching file
                    subtitle_file = subtitle_files[0]
                    logger.info(f'Extracting subtitle file: {subtitle_file}')

                    subtitle.content = fix_line_ending(zf.read(subtitle_file))
                    logger.info(f'Successfully extracted subtitle (size: {len(subtitle.content)} bytes)')
            else:
                # Regular subtitle file
                subtitle.content = fix_line_ending(response.content)
                logger.info(f'Successfully downloaded subtitle (size: {len(response.content)} bytes)')

        except Exception as e:
            logger.error(f'Error downloading subtitle: {e}')
