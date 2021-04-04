namespace SocketIOType {
  type Event =
    | "movie"
    | "series"
    | "episode"
    | "episode-history"
    | "movie-history"
    | "episode-blacklist"
    | "movie-blacklist"
    | "badges-movies"
    | "badges-series"
    | "badges-providers"
    | "task";

  type Action = "update" | "insert" | "delete";

  interface Body {
    type: Event;
    action: Action;
    id: number | null;
  }
}
