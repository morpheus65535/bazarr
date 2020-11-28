// State
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

interface AsyncState<T> {
  updating: boolean;
  lastResult?: string;
  items: T;
}

interface SystemState {
  languages: AsyncState<Array<Language>>;
  enabledLanguage: Array<Language>;
  status: AsyncState<SystemStatusResult>;
  tasks: AsyncState<Array<SystemTaskResult>>;
}

interface SeriesState {
  seriesList: AsyncState<Array<Series>>;
  wantedSeriesList: AsyncState<Array<WantedSeries>>;
}

interface MovieState {
  movieList: AsyncState<Array<Movie>>;
}
