declare namespace Task {
  type AnyCallable = (...args: never[]) => Promise<void>;
  export type Callable<T extends AnyCallable = AnyCallable> = T & {
    parameters: Parameters<T>;
    description: string;
    id: string;
  };

  export type Ref = string;
}
