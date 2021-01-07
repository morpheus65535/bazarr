type ValueOf<D> = D[keyof D];

type Unpacked<D> = D extends any[] ? D[number] : D;
