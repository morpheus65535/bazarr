export function defaultAOS(): AsyncOrderState<any> {
  return {
    updating: true,
    data: {
      items: [],
      order: [],
      fetched: false,
    },
  };
}
