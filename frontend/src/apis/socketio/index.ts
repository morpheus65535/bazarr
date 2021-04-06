import { debounce, uniq } from "lodash";
import { io, Socket } from "socket.io-client";
import { siteUpdateOffline } from "../../@redux/actions";
import reduxStore from "../../@redux/store";
import { log } from "../../utilites/logger";
import { SocketIOReducer } from "./reducer";

export class SocketIOClient {
  private socket: Socket;
  private events: SocketIO.Event[];
  private debounceReduce: () => void;

  constructor(baseUrl: string) {
    this.socket = io({
      path: `${baseUrl}socket.io`,
      transports: ["websocket", "polling"],
    });

    this.socket.on("connect", this.onConnect.bind(this));
    this.socket.on("disconnect", this.onDisconnect.bind(this));
    this.socket.on("data", this.onDataEvent.bind(this));

    this.events = [];
    this.debounceReduce = debounce(this.reduce, 200);
  }

  reconnect() {
    this.socket.connect();
  }

  private reduce() {
    const events = [...this.events];
    this.events = [];

    const store = reduxStore.getState();

    const records: SocketIO.ActionRecord = {};

    events.forEach((e) => {
      if (!(e.type in records)) {
        records[e.type] = {};
      }
      const record = records[e.type]!;
      if (!(e.action in record)) {
        record[e.action] = [];
      }
      if (e.id) {
        record[e.action]?.push(e.id);
      }
    });

    for (const key in records) {
      const type = key as SocketIO.Type;
      const element = records[type]!;

      const handler = SocketIOReducer.find((v) => v.key === type);
      if (handler) {
        if (handler.state && handler.state(store).updating) {
          return;
        }

        for (const actionKey in element) {
          const action = actionKey as SocketIO.Action;
          const ids = uniq(element[action]!);
          if (action in handler) {
            const realAction = handler[action]!();
            if (ids.length === 0) {
              reduxStore.dispatch(realAction());
            } else {
              reduxStore.dispatch(realAction(ids));
            }
          } else {
            log("error", "Unhandle action of SocketIO event", action, type);
          }
        }
      } else {
        log("error", "Unhandle SocketIO event", type);
      }
    }
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

  private onDataEvent(event: SocketIO.Event) {
    log("info", "Socket.IO receives", event);
    this.events.push(event);
    this.debounceReduce();
  }
}
