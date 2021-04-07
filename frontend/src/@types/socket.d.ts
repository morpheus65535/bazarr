namespace SocketIO {
  type Type =
    | "movie"
    | "series"
    | "episode"
    | "episode-history"
    | "movie-history"
    | "episode-blacklist"
    | "movie-blacklist"
    | "badges"
    | "task"
    | "settings"
    | "languages";

  type Action = "update" | "insert" | "delete";

  interface Event {
    type: Type;
    action: Action;
    id: number | null;
  }

  type ReducerAction = () => (id?: number[]) => any;

  type Reducer = {
    key: Type;
    state?: (store: ReduxStore) => AsyncState<any>;
  } & Partial<Record<Action, ReducerAction>>;

  type ActionRecord = OptionalRecord<Type, OptionalRecord<Action, number[]>>;
}
