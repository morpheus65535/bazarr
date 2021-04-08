namespace SocketIO {
  type EventType =
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

  type IdAction = (id?: number[]) => any;

  type Reducer = {
    key: EventType;
    state?: (store: ReduxStore) => AsyncState<any>;
    any?: Factory<() => any>;
  } & Partial<Record<ActionType, Factory<IdAction>>>;

  type ActionRecord = OptionalRecord<
    EventType,
    OptionalRecord<ActionType, number[]>
  >;
}
