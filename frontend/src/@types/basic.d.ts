type PythonBoolean = "True" | "False";

// Sonarr
type SonarrSeriesType = "Standard" | "Daily" | "Anime";

// Helper
interface DataWrapper<T> {
  data: T;
}