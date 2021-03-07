// Sonarr
type SonarrSeriesType = "Standard" | "Daily" | "Anime";

type PythonBoolean = "True" | "False";

type FileTree = {
  children: boolean;
  path: string;
  name: string;
};

type StorageType = string | null;

interface AsyncState<T> {
  updating: boolean;
  error?: Error;
  items: T;
}

type AsyncPayload<T> = T extends AsyncState<infer D> ? D : never;

type SelectorOption<PAYLOAD> = {
  label: string;
  value: PAYLOAD;
};

type SelectorValueType<T, M extends boolean> = M extends true
  ? ReadonlyArray<T>
  : Nullable<T>;
