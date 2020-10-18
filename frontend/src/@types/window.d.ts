declare global {
  interface Window {
    Bazarr: BazarrServer;
  }
}

export interface BazarrServer {
  apikey: string;
}
