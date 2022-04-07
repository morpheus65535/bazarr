declare namespace Task {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  type AnyCallable = (...args: any[]) => Promise<void>;
  export type Callable<T extends AnyCallable = AnyCallable> = T & {
    parameters: Parameters<T>;
    description: string;
  };

  export interface Group {
    description: string;
    notify: string;
  }
}
