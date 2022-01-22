declare namespace Server {
  interface Notification {
    type: "error" | "warning" | "info";
    id: string;
    message: string;
    timeout: number;
  }
}

declare namespace Site {
  type Status = "uninitialized" | "unauthenticated" | "initialized" | "error";
  interface Progress {
    id: string;
    header: string;
    name: string;
    value: number;
    count: number;
  }
}
