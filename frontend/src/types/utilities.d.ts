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

type Pair<T = string> = {
  key: string;
  value: T;
};

type EntityStruct<T> = {
  keyName: keyof T;
  ids: (string | null)[];
  entities: {
    [id: string]: T;
  };
};

interface DataWrapper<T> {
  data: T;
}

interface DataWrapperWithTotal<T> {
  data: T[];
  total: number;
}

type Override<T, U> = T & Omit<U, keyof T>;

type Comparer<T> = (lhs: T, rhs: T) => boolean;

type OptionalRecord<T extends string | number, D> = { [P in T]?: D };

interface IdState<T> {
  [key: number]: Readonly<T>;
}
