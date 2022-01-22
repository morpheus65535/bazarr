declare namespace Task {
  type Callable = (...args: any[]) => Promise<void>;

  interface Task<FN extends Callable> {
    name: string;
    id?: number;
    callable: FN;
    parameters: Parameters<FN>;
  }

  type Group = {
    [category: string]: Task.Task<Callable>[];
  };
}
