import type { PlexServer } from "@/plex/queries/plex";

interface ServerCacheData {
  selectedServer?: PlexServer | null;
  lastFetch?: number;
}

class PlexServerCache {
  private cache: ServerCacheData = {};

  getSelectedServer(): PlexServer | null | undefined {
    return this.cache.selectedServer;
  }

  setSelectedServer(server: PlexServer | null): void {
    this.cache.selectedServer = server;
  }

  getLastFetch(): number | undefined {
    return this.cache.lastFetch;
  }

  setLastFetch(timestamp: number): void {
    this.cache.lastFetch = timestamp;
  }

  shouldThrottleFetch(throttleMs: number = 30000): boolean {
    const now = Date.now();
    const lastFetch = this.cache.lastFetch;
    return !!(lastFetch && now - lastFetch < throttleMs);
  }

  clear(): void {
    this.cache = {};
  }
}

// Create a singleton instance
export const plexServerCache = new PlexServerCache();
