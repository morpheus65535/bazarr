namespace SocketIO {
  type EventType =
    | "connect"
    | "disconnect"
    | "movie"
    | "series"
    | "episode"
    | "episode-history"
    | "episode-blacklist"
    | "episode-wanted"
    | "movie-history"
    | "movie-blacklist"
    | "movie-wanted"
    | "badges"
    | "task"
    | "settings"
    | "languages";

  type ActionType = "update" | "delete";

  interface Event {
    type: EventType;
    action: ActionType;
    id: number | null;
  }

  type ActionFn = (id?: number[]) => void;

  type Reducer = {
    key: EventType;
    state?: (store: ReduxStore) => AsyncState<any>;
    any?: () => any;
  } & Partial<Record<ActionType, ActionFn>>;

  type ActionRecord = OptionalRecord<
    EventType,
    OptionalRecord<ActionType, number[]>
  >;
}
