declare namespace Server {
  interface Notification {
    type: "error" | "warning" | "info";
    id: string;
    message: string;
    timeout: number;
  }
}

declare namespace Site {
  interface Progress {
    id: string;
    header: string;
    name: string;
    value: number;
    count: number;
  }
}
