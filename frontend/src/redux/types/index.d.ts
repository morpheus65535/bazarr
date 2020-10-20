// State
interface StoreState {
  badges: BadgeState;
  system: SystemState;
  series: SeriesState;
}

interface BadgeState {
  movies: number;
  episodes: number;
  providers: number;
}

interface AsyncState<T> {
  loading: boolean;
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
}
