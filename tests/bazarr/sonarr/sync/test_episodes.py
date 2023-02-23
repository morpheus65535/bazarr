from app.database import TableEpisodes
from sonarr.sync.episodes import sync_one_episode

sonarr_response = {
  'seriesId': 1,
  'episodeFileId': 118111,
  'seasonNumber': 1,
  'episodeNumber': 1,
  'title': 'test',
  'overview': "test.",
  'episodeFile': {
    'seriesId': 1,
    'seasonNumber': 1,
    'path': "/test/Season 1/test.avi",
    'size': 416622404,
    'languages': [
      {
        'id': 1,
        'name': 'English'
      }
    ],
    'quality': {
      'quality': {
        'id': 1,
        'name': 'SDTV',
        'source': 'television',
        'resolution': 480
      },
      'revision': {
        'version': 1,
        'real': 0,
        'isRepack': False
      }
    },
    'mediaInfo': {
      'audioBitrate': 160000,
      'audioChannels': 2,
      'audioCodec': 'AC3',
      'audioLanguages': '',
      'audioStreamCount': 1,
      'videoBitDepth': 8,
      'videoBitrate': 1145722,
      'videoCodec': '',
      'videoFps': 25,
      'videoDynamicRange': '',
      'videoDynamicRangeType': '',
      'resolution': '720x400',
      'runTime': '42:11',
      'scanType': 'Progressive',
      'subtitles': ''
    },
    'qualityCutoffNotMet': True,
    'id': 118111
  },
  'hasFile': True,
  'monitored': False,
  'absoluteEpisodeNumber': 1,
  'unverifiedSceneNumbering': False,
  'grabbed': False,
  'id': 8
}


def test_sync_one_episode_add(mocker, db):
    mocker.patch('sonarr.sync.episodes.get_episodes_from_sonarr_api', return_value=sonarr_response)
    mocker.patch('sonarr.sync.episodes.get_episodesFiles_from_sonarr_api', return_value=sonarr_response['episodeFile'])
    mocker.patch("sonarr.sync.episodes.get_sonarr_info.is_legacy", return_value=False)
    mocker.patch('sonarr.sync.episodes.event_stream')
    # Arrange
    episode_id = 8
    # Act
    sync_one_episode(episode_id)
    # Assert
    assert TableEpisodes.select().count() == 1
    result = TableEpisodes.select().where(TableEpisodes.sonarrEpisodeId == episode_id).first()
    assert result.sonarrEpisodeId == 8
    assert result.sonarrSeriesId == 1
    assert result.title == 'test'
    assert result.path == "/test/Season 1/test.avi"
    assert result.season == 1
    assert result.episode == 1
    assert result.subtitles is None
    assert result.audio_codec == "AC3"
    assert result.audio_language == "[]"
    assert result.episode_file_id == 118111
    assert result.file_size == 416622404
    assert result.format == "SDTV"
    assert result.monitored == "False"
    assert result.resolution == "480p"
    assert result.sceneName is None


def test_sync_one_episode_update(mocker, db):
    sonarr_response['title'] = 'test2'
    mocker.patch('sonarr.sync.episodes.get_episodes_from_sonarr_api', return_value=sonarr_response)
    mocker.patch('sonarr.sync.episodes.get_episodesFiles_from_sonarr_api', return_value=sonarr_response['episodeFile'])
    mocker.patch("sonarr.sync.episodes.get_sonarr_info.is_legacy", return_value=False)
    mocker.patch('sonarr.sync.episodes.event_stream')
    # Arrange
    episode_id = 8
    assert TableEpisodes.select().count() == 1
    # Act
    sync_one_episode(episode_id)
    # Assert
    assert TableEpisodes.select().count() == 1
    result = TableEpisodes.select().where(TableEpisodes.sonarrEpisodeId == episode_id).first()
    assert result.sonarrEpisodeId == 8
    assert result.sonarrSeriesId == 1
    assert result.title == 'test2'
    # assert result.path == "/test/Season 1/test.avi"
    assert result.season == 1
    assert result.episode == 1
    assert result.subtitles is None
    assert result.audio_codec == "AC3"
    assert result.audio_language == "[]"
    assert result.episode_file_id == 118111
    assert result.file_size == 416622404
    assert result.format == "SDTV"
    assert result.monitored == "False"
    assert result.resolution == "480p"
    assert result.sceneName is None


def test_sync_one_episode_remove(mocker, db):
    mocker.patch('sonarr.sync.episodes.get_episodes_from_sonarr_api', return_value={})
    mocker.patch('sonarr.sync.episodes.get_episodesFiles_from_sonarr_api', return_value=sonarr_response['episodeFile'])
    mocker.patch("sonarr.sync.episodes.get_sonarr_info.is_legacy", return_value=False)
    mocker.patch('sonarr.sync.episodes.event_stream')
    # Arrange
    episode_id = 8
    assert TableEpisodes.select().count() == 1
    # Act
    sync_one_episode(episode_id)
    # Assert
    assert TableEpisodes.select().count() == 0
    result = TableEpisodes.select().where(TableEpisodes.sonarrEpisodeId == episode_id).first()
    assert result is None
