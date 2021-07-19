interface SocketIODebugger {
  dump: () => void;
  emit: (event: SocketIO.Event) => void;
}

declare global {
  interface Window {
    Bazarr: BazarrServer;
    _socketio: SocketIODebugger;
  }
}

export interface BazarrServer {
  baseUrl: string;
  apiKey?: string;
  canUpdate: boolean;
  hasUpdate: boolean;
}
