interface AsyncState<T> {
  updating: boolean;
  lastResult?: string;
  items: T;
}

interface StoreState {
  badges: BadgeState;
  system: SystemState;
  series: SeriesState;
  movie: MovieState;
}

interface BadgeState {
  movies: number;
  episodes: number;
  providers: number;
}

interface SystemState {
  languages: AsyncState<Array<ExtendLanguage>>;
  enabledLanguage: Array<ExtendLanguage>;
  status: AsyncState<SystemStatusResult>;
  tasks: AsyncState<Array<SystemTaskResult>>;
  providers: AsyncState<Array<SystemProviders>>;
}

interface SeriesState {
  seriesList: AsyncState<Array<Series>>;
  wantedSeriesList: AsyncState<Array<WantedEpisode>>;
  episodeList: AsyncState<Map<number, Array<Episode>>>;
  historyList: AsyncState<Array<SeriesHistory>>;
}

interface MovieState {
  movieList: AsyncState<Array<Movie>>;
  wantedMovieList: AsyncState<Array<WantedMovie>>;
  historyList: AsyncState<Array<MovieHistory>>;
}
