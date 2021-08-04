export function defaultAOS(): AsyncOrderState<any> {
  return {
    state: "idle",
    data: {
      items: [],
      order: [],
      dirty: false,
    },
  };
}
