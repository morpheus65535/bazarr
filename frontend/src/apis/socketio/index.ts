import { io, Socket } from "socket.io-client";
import {
  badgeUpdateAll,
  movieUpdateBlacklist,
  movieUpdateHistoryList,
  seriesUpdateBlacklist,
  seriesUpdateHistoryList,
  siteUpdateOffline,
  systemUpdateTasks,
} from "../../@redux/actions";
import reduxStore from "../../@redux/store";
import { log } from "../../utilites/logger";

export class SocketIOClient {
  private socket: Socket;

  constructor(baseUrl: string) {
    this.socket = io({
      path: `${baseUrl}socket.io`,
      transports: ["websocket", "polling"],
    });

    this.socket.on("connect", this.onConnect.bind(this));
    this.socket.on("disconnect", this.onDisconnect.bind(this));
    this.socket.on("data", this.onDataEvent.bind(this));
  }

  reconnect() {
    this.socket.connect();
  }

  private dispatch(action: any, state?: AsyncState<any>) {
    const canDispatch = state ? state.updating === false : true;
    if (canDispatch) {
      reduxStore.dispatch(action);
    }
  }

  private onConnect() {
    log("info", "Socket.IO has connected");
    this.dispatch(siteUpdateOffline(false));
  }

  private onDisconnect() {
    log("warning", "Socket.IO has disconnected");
    this.dispatch(siteUpdateOffline(true));
  }

  private onDataEvent(event: SocketIOType.Body) {
    log("info", "Socket.IO receives", event);
    const store = reduxStore.getState();
    switch (event.type) {
      case "badges":
        this.dispatch(badgeUpdateAll());
        break;
      case "task":
        this.dispatch(systemUpdateTasks(), store.system.tasks);
        break;
      case "episode-blacklist":
        this.dispatch(seriesUpdateBlacklist(), store.series.blacklist);
        break;
      case "movie-blacklist":
        this.dispatch(movieUpdateBlacklist(), store.movie.blacklist);
        break;
      case "episode-history":
        this.dispatch(seriesUpdateHistoryList(), store.series.historyList);
        break;
      case "movie-history":
        this.dispatch(movieUpdateHistoryList(), store.movie.historyList);
        break;
      default:
        log("error", "SocketIO receives a unhandle event", event);
    }
  }
}
