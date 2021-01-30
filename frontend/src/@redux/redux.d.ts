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
  site: SiteState;
}

interface SiteState {
  initialized: boolean;
  auth: boolean;
}

interface BadgeState {
  movies: number;
  episodes: number;
  providers: number;
}

interface SystemState {
  languages: AsyncState<Array<Language>>;
  enabledLanguage: AsyncState<Array<Language>>;
  languagesProfiles: AsyncState<Array<LanguagesProfile>>;
  status: AsyncState<SystemStatusResult | undefined>;
  tasks: AsyncState<Array<SystemTaskResult>>;
  providers: AsyncState<Array<SystemProvider>>;
  logs: AsyncState<Array<SystemLog>>;
  releases: AsyncState<Array<ReleaseInfo>>;
  settings: AsyncState<SystemSettings | undefined>;
}

interface SeriesState {
  seriesList: AsyncState<Array<Series>>;
  wantedSeriesList: AsyncState<Array<WantedEpisode>>;
  episodeList: AsyncState<Map<number, Array<Episode>>>;
  historyList: AsyncState<Array<SeriesHistory>>;
  blacklist: AsyncState<Array<SeriesBlacklist>>;
}

interface MovieState {
  movieList: AsyncState<Array<Movie>>;
  wantedMovieList: AsyncState<Array<WantedMovie>>;
  historyList: AsyncState<Array<MovieHistory>>;
  blacklist: AsyncState<Array<MovieBlacklist>>;
}
