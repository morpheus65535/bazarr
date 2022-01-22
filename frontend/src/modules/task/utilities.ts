export function createTask<T extends Task.Callable>(
  name: string,
  id: number | undefined,
  callable: T,
  ...parameters: Parameters<T>
): Task.Task<T> {
  return {
    name,
    id,
    callable,
    parameters,
  };
}
