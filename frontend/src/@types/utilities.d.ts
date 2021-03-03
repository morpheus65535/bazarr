type ValueOf<D> = D[keyof D];

type Unpacked<D> = D extends any[] ? D[number] : D;

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

type ArrayElement<T extends unknown[]> = T extends (infer D)[] ? D : never;

interface DataWrapper<T> {
  data: T;
}

type PromiseType<T> = T extends Promise<infer D> ? D : never;

interface AsyncState<T> {
  updating: boolean;
  error?: Error;
  items: T;
}

type AsyncPayload<T> = T extends AsyncState<infer D> ? D : never;

type Override<T, U> = T & Omit<U, keyof T>;

type SelectorOption<PAYLOAD> = {
  label: string;
  value: PAYLOAD;
};

type SelectorValueType<T, M extends boolean> = M extends true
  ? ReadonlyArray<T>
  : T | undefined;

type Comparer<T> = (lhs: T, rhs: T) => boolean;
