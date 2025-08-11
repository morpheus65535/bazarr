// Deprecated: serverCache no longer used after frontend streamlining.
// Intentionally left minimal to avoid breaking lingering imports.
export const plexServerCache = {
  getSelectedServer: () => null,
  setSelectedServer: () => void 0,
  shouldThrottleFetch: () => false,
  setLastFetch: () => void 0,
};
