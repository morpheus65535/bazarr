// State
export interface StoreState {
  badges: BadgeState;
  system: SystemState;
  series: SeriesState;
}

export interface BadgeState {
  movies: number;
  episodes: number;
  providers: number;
}

export interface AsyncState<T> {
  loading: boolean;
  lastResult?: string;
  items: T;
}

export interface SystemState {
  languages: AsyncState<Array<Language>>;
  status: AsyncState<SystemStatusResult>;
}

export interface SeriesState {
  seriesList: AsyncState<Array<Series>>;
}
