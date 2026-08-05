export const isMovie = (v: object): v is Item.Movie => "radarrId" in v;

export const isEpisode = (v: object): v is Item.Episode =>
  "sonarrEpisodeId" in v;

export const isSeries = (v: object): v is Item.Series =>
  "episodeFileCount" in v;
