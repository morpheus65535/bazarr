namespace SocketIO {
  type Action = "update" | "delete";

  type EventType = NumEventType | NullEventType | SpecialEventType;

  type NumEventType =
    | "movie"
    | "series"
    | "episode"
    | "episode-wanted"
    | "movie-wanted";

  type NullEventType =
    | "connect"
    | "connect_error"
    | "disconnect"
    | "episode-blacklist"
    | "episode-history"
    | "movie-blacklist"
    | "movie-history"
    | "badges"
    | "task"
    | "settings"
    | "languages";

  type SpecialEventType = "message" | "progress";

  type ReducerCreator<E extends EventType, T> = ValueOf<
    {
      [P in E]: {
        key: P;
        any?: () => void;
      } & Partial<Record<Action, ActionFn<T>>>;
    }
  >;

  type Event = {
    type: EventType;
    action: Action;
    payload: any;
  };

  type ActionFn<T> = (payload?: T[]) => void;

  type Reducer =
    | ReducerCreator<NumEventType, number>
    | ReducerCreator<NullEventType, null>
    | ReducerCreator<"message", string>
    | ReducerCreator<"progress", CustomEvent.Progress>;

  type ActionRecord = OptionalRecord<EventType, OptionalRecord<Action, any[]>>;

  namespace CustomEvent {
    type Progress = ReduxStore.Progress;
  }
}
