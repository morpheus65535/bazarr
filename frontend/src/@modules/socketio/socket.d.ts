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

  type SpecialEventType = "message" | "progress";

  type ActionType = "update" | "delete";

  type ReducerCreator<E extends EventType, U, D = U> = ValueOf<
    {
      [P in E]: {
        key: P;
        any?: ActionHandler<null>;
        update?: ActionHandler<U>;
        delete?: ActionHandler<D>;
      };
    }
  >;

  type Event = {
    type: EventType;
    action: ActionType;
    payload: any;
  };

  type ActionHandler<T> = T extends null ? () => void : (payload: T[]) => void;

  type Reducer =
    | ReducerCreator<NumEventType, number>
    | ReducerCreator<NullEventType, null>
    | ReducerCreator<"message", string>
    | ReducerCreator<"progress", CustomEvent.Progress, string>;

  type ActionRecord = {
    [P in EventType]?: {
      [R in ActionType]?: any[];
    };
  };

  namespace CustomEvent {
    type Progress = Site.Progress;
  }
}
