type ValueOf<D> = D[keyof D];

type Unpacked<D> = D extends unknown[] | readonly unknown[] ? D[number] : D;

type Nullable<D> = D | null;

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
