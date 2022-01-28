declare namespace Task {
  type Callable<P> = (...args: P) => Promise<void>;

  interface Task<P, FN extends Callable<P>> {
    name: string;
    id?: number;
    callable: FN;
    parameters: P;
  }

  type Group = {
    [category: string]: Task.Task<Callable>[];
  };
}
