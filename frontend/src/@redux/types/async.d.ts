declare namespace Async {
  type State = "loading" | "succeeded" | "failed" | "dirty" | "idle";

  type IdType = number | string;

  type BaseType<T> = {
    state: State;
    content: T;
    error: string | null;
  };

  type List<T> = BaseType<T[]> & {
    dirtyEntities: IdType[];
  };

  type Item<T> = BaseType<T | null>;

  type Entity<T> = BaseType<EntityStruct<T>> & {
    dirtyEntities: string[];
  };
}
