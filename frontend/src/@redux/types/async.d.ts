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

  type EntityStruct<T> = {
    keyName: keyof T;
    ids: (string | null)[];
    entities: {
      [id: string]: T;
    };
  };

  // TODO: only number temporarily
  type Entity<T> = BaseType<EntityStruct<T>> & {
    dirtyEntities: string[];
  };
}
