interface SocketIODebugger {
  dump: () => void;
  emit: (event: SocketIO.Event) => void;
}

declare global {
  interface Window {
    Bazarr: BazarrServer;
    socketIO: SocketIODebugger;
  }

  interface WindowEventMap {
    "app-auth-changed": CustomEvent<{ authenticated: boolean }>;
    "app-critical-error": CustomEvent<{ message: string }>;
    "app-online-status": CustomEvent<{ online: boolean }>;
  }
}

export interface BazarrServer {
  baseUrl: string;
  apiKey?: string;
  canUpdate: boolean;
  hasUpdate: boolean;
}
