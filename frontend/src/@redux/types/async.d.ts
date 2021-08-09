declare namespace Async {
  type State = "loading" | "succeeded" | "failed" | "dirty" | "uninitialized";

  type IdType = number | string;

  type Base<T> = {
    state: State;
    content: T;
    error: string | null;
  };

  type List<T> = Base<T[]> & {
    dirtyEntities: IdType[];
  };

  type Item<T> = Base<T | null>;

  type Entity<T> = Base<EntityStruct<T>> & {
    dirtyEntities: string[];
  };
}
