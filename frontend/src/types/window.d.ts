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
    "bazarr-settings-saved": Event;
  }
}

export interface BazarrServer {
  baseUrl: string;
  apiKey?: string;
  canUpdate: boolean;
  hasUpdate: boolean;
  isConfigured: boolean;
}
