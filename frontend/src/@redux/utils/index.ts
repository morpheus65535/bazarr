export function defaultAOS(): AsyncOrderState<any> {
  return defaultAS({
    items: [],
    order: [],
    dirty: false,
  });
}

export function defaultAS<T>(value: T): AsyncState<T> {
  return {
    state: "idle",
    data: value,
  };
}
