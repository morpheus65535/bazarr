import { useLocalStorage } from "@mantine/hooks";

export type ViewMode = "table" | "poster";

export const seriesViewModeKey = "series-view-mode";
export const moviesViewModeKey = "movies-view-mode";
export const sportsViewModeKey = "sports-view-mode";

// Persists the list view mode (table/poster) in the browser so it survives
// restarts. Reads synchronously on mount to avoid flashing the table view
// before switching to a persisted poster view.
export const useViewMode = (key: string) => {
  return useLocalStorage<ViewMode>({
    key,
    defaultValue: "table",
    getInitialValueInEffect: false,
  });
};
