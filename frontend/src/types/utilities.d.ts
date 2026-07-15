type ValueOf<D> = D[keyof D];

type Unpacked<D> = D extends unknown[] | readonly unknown[] ? D[number] : D;

type Nullable<D> = D | null;

type CamelCase<S extends string> = S extends `${infer Head}_${infer Tail}`
  ? `${Head}${CamelCase<Capitalize<Tail>>}`
  : S;

type CamelCaseKeys<T> =
  T extends ReadonlyArray<infer U>
    ? CamelCaseKeys<U>[]
    : T extends Date
      ? T
      : T extends File
        ? T
        : T extends Blob
          ? T
          : T extends RegExp
            ? T
            : T extends (...args: unknown[]) => unknown
              ? T
              : T extends object
                ? {
                    [K in keyof T as CamelCase<K & string>]: CamelCaseKeys<
                      T[K]
                    >;
                  }
                : T;

type LooseObject = {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  [key: string]: any;
};

type StrictObject<T> = {
  [key: string]: T;
};

interface DataWrapper<T> {
  data: T;
}

interface DataWrapperWithTotal<T> {
  data: T[];
  total: number;
}

type Override<T, U> = T & Omit<U, keyof T>;

type Sure<T> = Exclude<T, null | undefined>;

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type GenericFunction<T = void> = (...args: any[]) => T;
