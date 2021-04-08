import { debounce, forIn, isUndefined, uniq } from "lodash";
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

  private dispatch(action: (ids?: number[]) => any, ids?: number[]) {
    if (isUndefined(ids)) {
      reduxStore.dispatch(action());
    } else {
      reduxStore.dispatch(action(ids));
    }
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

    forIn(records, (element, type) => {
      if (element) {
        const handlers = SocketIOReducer.filter((v) => v.key === type);
        if (handlers.length === 0) {
          log("error", "Unhandle SocketIO event", type);
          return;
        }

        // eslint-disable-next-line no-loop-func
        handlers.forEach((handler) => {
          if (handler.state && handler.state(store).updating) {
            return;
          }

          const anyAction = handler.any;
          if (anyAction) {
            this.dispatch(anyAction());
            return;
          }

          forIn(element, (ids, key) => {
            ids = uniq(ids);
            const action = handler[key as SocketIO.ActionType];
            if (action) {
              this.dispatch(action());
            } else {
              log("error", "Unhandle action of SocketIO event", key, type);
            }
          });
        });
      }
    });
  }

  private onConnect() {
    log("info", "Socket.IO has connected");
    reduxStore.dispatch(siteUpdateOffline(false));
  }

  private onDisconnect() {
    log("warning", "Socket.IO has disconnected");
    reduxStore.dispatch(siteUpdateOffline(true));
  }

  private onDataEvent(event: SocketIO.Event) {
    log("info", "Socket.IO receives", event);
    this.events.push(event);
    this.debounceReduce();
  }
}
