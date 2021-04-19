declare global {
  interface Window {
    Bazarr: BazarrServer;
    DumpSocketIO: () => void;
  }
}

export interface BazarrServer {
  baseUrl: string;
  apiKey: string;
  canUpdate: boolean;
  hasUpdate: boolean;
}
