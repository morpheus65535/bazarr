interface SocketIODebugger {
  dump: () => void;
  emit: (event: SocketIO.Event) => void;
}

declare global {
  interface Window {
    Bazarr: BazarrServer;
    _socketio: SocketIODebugger;
  }

  interface WindowEventMap {
    "app-critical-error": CustomEvent<{ message: string }>;
    "app-login-required": CustomEvent;
    "app-online-status": CustomEvent<{ online: boolean }>;
  }
}

export interface BazarrServer {
  baseUrl: string;
  apiKey?: string;
  canUpdate: boolean;
  hasUpdate: boolean;
}
