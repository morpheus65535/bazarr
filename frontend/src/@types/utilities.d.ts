type ValueOf<D> = D[keyof D];

type Unpacked<D> = D extends any[] ? D[number] : D;

type LooseObject = {
  [key: string]: any;
};

type Pair = {
  key: string;
  value: string;
};

interface DataWrapper<T> {
  data: T;
}

type PromiseType<T> = T extends Promise<infer D> ? D : T;
