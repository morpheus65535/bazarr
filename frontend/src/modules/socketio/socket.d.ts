declare namespace SocketIO {
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
    | "reset-episode-wanted"
    | "reset-movie-wanted"
    | "badges"
    | "task"
    | "settings"
    | "languages";

  type SpecialEventType = "message" | "progress" | "jobs";

  type ActionType = "update" | "delete";

  type PayloadType = number | string | CustomEvent.Progress;

  type ReducerGroup<
    E extends EventType,
    U extends PayloadType | undefined,
    D = U,
  > = ValueOf<{
    [P in E]: {
      key: P;
      any?: ActionHandler<undefined>;
      update?: ActionHandler<U>;
      delete?: ActionHandler<D>;
    };
  }>;

  type Event = {
    type: EventType;
    action: ActionType;
    payload?: PayloadType;
  };

  type ActionHandler<T> = T extends undefined
    ? () => void
    : (payload: T[]) => void;

  type Reducer =
    | ReducerGroup<NumEventType, number>
    | ReducerGroup<NullEventType, undefined>
    | ReducerGroup<"jobs", CustomEvent.Jobs, string>
    | ReducerGroup<"message", string>
    | ReducerGroup<"progress", CustomEvent.Progress, string>;

  type ActionRecord = {
    [P in EventType]?: {
      [R in ActionType]?: PayloadType[];
    };
  };

  namespace CustomEvent {
    type Progress = Site.Progress;
    type Jobs = Manager.Jobs;
  }
}
