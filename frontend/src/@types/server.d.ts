namespace Server {
  interface Notification {
    type: "error" | "warning" | "info";
    id: string;
    message: string;
    timeout: number;
  }

  interface Progress {
    id: string;
    header: string;
    name: string;
    value: number;
    count: number;
  }
}
