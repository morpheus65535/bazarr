export function createTask<R, T extends Task.Callable<R>>(
  name: string,
  id: number | undefined,
  callable: T,
  parameters: R
): Task.Task<R, T> {
  return {
    name,
    id,
    callable,
    parameters,
  };
}
