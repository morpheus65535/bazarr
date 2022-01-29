declare namespace Task {
  type Status = "idle" | "running" | "success" | "failure";

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  type AnyCallable = (...args: any[]) => Promise<void>;
  export type Callable<T extends AnyCallable = AnyCallable> = T & {
    parameters: Parameters<T>;
    id: string;
    status: Status;
  };

  export interface Task {
    name: string;
    callableId: string;
    description?: string;
  }
}
