export interface BaseAction {
  type: string;
}

export interface UpdateMoviesAction extends BaseAction {
  value: number;
}

export interface UpdateEpisodesAction extends BaseAction {
  value: number;
}

export interface UpdateProvidersAction extends BaseAction {
  value: number;
}

export type UpdateBadgeAction =
  | UpdateMoviesAction
  | UpdateEpisodesAction
  | UpdateProvidersAction;
