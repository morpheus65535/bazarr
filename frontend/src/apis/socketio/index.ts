import { io, Socket } from "socket.io-client";
import { DefaultEventsMap } from "socket.io-client/build/typed-events";
import { log } from "../../utilites/logger";

export class SocketIOClient {
  socket: Socket<DefaultEventsMap, DefaultEventsMap>;

  constructor(baseUrl: string) {
    this.socket = io({
      path: `${baseUrl}socket.io`,
      transports: ["websocket", "polling"],
    });

    this.socket.onAny(this.onEvent);
  }

  onEvent(eventName: string, ...args: any[]) {
    log("info", "Socket.IO receives event", eventName, args);
  }
}
