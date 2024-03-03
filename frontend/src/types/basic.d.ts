// Sonarr
type SonarrSeriesType = "Standard" | "Daily" | "Anime";

type PythonBoolean = "True" | "False";

type FileTree = {
  children: boolean;
  path: string;
  name: string;
};

type StorageType = string | null;

type SimpleStateType<T> = [
  T,
  ((item: T) => void) | ((fn: (item: T) => T) => void),
];

type Factory<T> = () => T;

type MantineComp<T, C> = T & Omit<React.ComponentProps<C>, "ref">;
