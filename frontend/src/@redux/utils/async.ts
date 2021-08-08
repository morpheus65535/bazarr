export namespace AsyncUtility {
  export function getDefaultItem<T>(): Async.Item<T> {
    return {
      state: "idle",
      content: null,
      error: null,
    };
  }

  export function getDefaultList<T>(): Async.List<T> {
    return {
      state: "idle",
      dirtyEntities: [],
      content: [],
      error: null,
    };
  }

  export function getDefaultEntity<T>(key: keyof T): Async.Entity<T> {
    return {
      state: "idle",
      dirtyEntities: [],
      content: {
        keyName: key,
        ids: [],
        entities: {},
      },
      error: null,
    };
  }
}
