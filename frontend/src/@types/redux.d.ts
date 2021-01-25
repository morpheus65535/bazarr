interface AsyncState<T> {
  updating: boolean;
  error?: string;
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
  initialized: boolean;
  languages: AsyncState<Array<Language>>;
  enabledLanguage: AsyncState<Array<Language>>;
  languagesProfiles: AsyncState<Array<LanguagesProfile>>;
  status: AsyncState<SystemStatusResult | undefined>;
  tasks: AsyncState<Array<SystemTaskResult>>;
  providers: AsyncState<Array<SystemProvider>>;
  logs: AsyncState<Array<SystemLog>>;
  settings: AsyncState<SystemSettings | undefined>;
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
