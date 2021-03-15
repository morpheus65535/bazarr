type ValueOf<D> = D[keyof D];

type Unpacked<D> = D extends any[] | readonly any[] ? D[number] : D;

type Nullable<D> = D | null;

type LooseObject = {
  [key: string]: any;
};

type StrictObject<T> = {
  [key: string]: T;
};

type Pair<T = string> = {
  key: string;
  value: T;
};

interface DataWrapper<T> {
  data: T;
}

interface AsyncDataWrapper<T> {
  data: T[];
  total: number;
}

type PromiseType<T> = T extends Promise<infer D> ? D : never;

type Override<T, U> = T & Omit<U, keyof T>;

type Comparer<T> = (lhs: T, rhs: T) => boolean;

type KeysOfType<D, T> = NonNullable<
  ValueOf<{ [P in keyof D]: D[P] extends T ? P : never }>
>;

type ItemIdType<T> = KeysOfType<T, number>;
