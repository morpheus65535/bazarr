type ValueOf<D> = D[keyof D];

type Unpacked<D> = D extends unknown[] | readonly unknown[] ? D[number] : D;

type Nullable<D> = D | null;

type CamelCase<S extends string> = S extends `${infer Head}_${infer Tail}`
  ? `${Head}${CamelCase<Capitalize<Tail>>}`
  : S;

type CamelCaseLeaf =
  Date | File | Blob | RegExp | ((...args: unknown[]) => unknown);

type CamelCaseKeys<T> =
  T extends ReadonlyArray<infer U>
    ? CamelCaseKeys<U>[]
    : T extends CamelCaseLeaf
      ? T
      : T extends object
        ? { [K in keyof T as CamelCase<K & string>]: CamelCaseKeys<T[K]> }
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

type GenericFunction<T = void> = (...args: never[]) => T;
