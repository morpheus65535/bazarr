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
    | "languages"
    | "message";

  type ActionType = "update" | "delete";

  interface Event {
    type: EventType;
    action: ActionType;
    payload: any; // TODO: Use specific types
  }

  type ActionFn = (payload?: any[]) => void;

  type Reducer = {
    key: EventType;
    any?: () => any;
  } & Partial<Record<ActionType, ActionFn>>;

  type ActionRecord = OptionalRecord<
    EventType,
    OptionalRecord<ActionType, any[]>
  >;
}
