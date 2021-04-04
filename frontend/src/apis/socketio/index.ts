import { io, Socket } from "socket.io-client";
import { DefaultEventsMap } from "socket.io-client/build/typed-events";
import { siteUpdateOffline } from "../../@redux/actions";
import reduxStore from "../../@redux/store";
import { log } from "../../utilites/logger";

export class SocketIOClient {
  socket: Socket<DefaultEventsMap, DefaultEventsMap>;

  constructor(baseUrl: string) {
    this.socket = io({
      path: `${baseUrl}socket.io`,
      transports: ["websocket", "polling"],
    });

    this.socket.on("connect", this.onConnect);
    this.socket.on("disconnect", this.onDisconnect);

    this.socket.onAny(this.onEvent);
  }

  onConnect() {
    log("info", "Socket.IO has connected");
    reduxStore.dispatch(siteUpdateOffline(false));
  }

  onDisconnect() {
    log("warning", "Socket.IO has disconnected");
    reduxStore.dispatch(siteUpdateOffline(true));
  }

  onEvent(eventName: string, ...args: any[]) {
    console.log("Socket.IO receives event", eventName, args);
  }
}
