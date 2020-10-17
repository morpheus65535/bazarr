// State
export interface StoreState {
  badges: BadgeState;
}

export interface BadgeState {
  movies: number;
  episodes: number;
  providers: number;
}
