type ValueOf<D> = D[keyof D];

type Unpacked<D> = D extends any[] ? D[number] : D;

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

type PromiseType<T> = T extends Promise<infer D> ? D : never;

type Override<T, U> = T & Omit<U, keyof T>;

type Comparer<T> = (lhs: T, rhs: T) => boolean;
