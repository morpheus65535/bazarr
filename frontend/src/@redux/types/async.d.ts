namespace Async {
  type State = "loading" | "succeeded" | "failed" | "dirty" | "idle";

  type IdType = number | string;

  type BaseType<T> = {
    state: State;
    content: T;
    error: Unknown | null;
  };

  type List<T> = BaseType<T[]> & {
    dirtyEntities: IdType[];
  };

  type Item<T> = BaseType<T | null>;

  type Pagination<T> = BaseType<{ [id: IdType]: T }> & {
    dirtyEntities: IdType[];
  };
}
