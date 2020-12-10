declare global {
  interface Window {
    Bazarr: BazarrServer;
  }
}

export interface BazarrServer {
  apiKey: string;
}
