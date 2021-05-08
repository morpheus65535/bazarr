declare global {
  interface Window {
    Bazarr: BazarrServer;
  }
}

export interface BazarrServer {
  baseUrl: string;
  apiKey?: string;
  canUpdate: boolean;
  hasUpdate: boolean;
}
