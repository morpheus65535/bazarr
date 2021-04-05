import { io, Socket } from "socket.io-client";
import { siteUpdateOffline } from "../../@redux/actions";
import reduxStore from "../../@redux/store";
import { log } from "../../utilites/logger";

export class SocketIOClient {
  socket: Socket;

  constructor(baseUrl: string) {
    this.socket = io({
      path: `${baseUrl}socket.io`,
      transports: ["websocket", "polling"],
    });

    this.socket.on("connect", this.onConnect.bind(this));
    this.socket.on("disconnect", this.onDisconnect);
    this.socket.on("data", this.onDataEvent);
  }

  onConnect() {
    log("info", "Socket.IO has connected");
    reduxStore.dispatch(siteUpdateOffline(false));
  }

  onDisconnect() {
    log("warning", "Socket.IO has disconnected");
    reduxStore.dispatch(siteUpdateOffline(true));
  }

  onDataEvent(event: SocketIOType.Body) {
    log("info", "Socket.IO receives", event);
  }
}
