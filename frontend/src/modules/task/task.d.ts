declare namespace Task {
  type Status = "idle" | "running" | "success" | "failure";

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  type AnyCallable = (...args: any[]) => Promise<void>;
  export type Callable<T extends AnyCallable = AnyCallable> = T & {
    parameters: Parameters<T>;
    id: symbol;
    status: Status;
  };

  export interface TaskRef {
    name: string;
    callableId: symbol;
    description?: string;
  }

  export interface Group {
    description: string;
    notify: string;
  }
}
