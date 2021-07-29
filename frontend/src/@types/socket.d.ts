namespace SocketIO {
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

  type ReducerCreator<E extends EventType, U, D = never> = ValueOf<
    {
      [P in E]: {
        key: P;
        any?: () => void;
        update?: ActionFn<T>;
        delete?: ActionFn<D extends never ? T : D>;
      } & LooseObject;
      // TODO: Typing
    }
  >;

  type Event = {
    type: EventType;
    action: string;
    payload: any;
  };

  type ActionFn<T> = (payload?: T[]) => void;

  type Reducer =
    | ReducerCreator<NumEventType, number>
    | ReducerCreator<NullEventType, null>
    | ReducerCreator<"message", string>
    | ReducerCreator<"progress", CustomEvent.Progress, string>;

  type ActionRecord = OptionalRecord<EventType, StrictObject<any[]>>;

  namespace CustomEvent {
    type Progress = Server.Progress;
  }
}
