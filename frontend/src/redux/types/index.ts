// State
export interface StoreState {
  badges: BadgeState;
  common: CommonState;
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

export interface CommonState {
  languages: AsyncState<Array<Language>>;
  series: AsyncState<Array<Series>>;
}
