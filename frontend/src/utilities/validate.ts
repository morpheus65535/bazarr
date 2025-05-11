export function isMovie(v: object): v is Item.Movie {
  return "radarrId" in v;
}

export function isEpisode(v: object): v is Item.Episode {
  return "sonarrEpisodeId" in v;
}

export function isSeries(v: object): v is Item.Series {
  return "episodeFileCount" in v;
}
