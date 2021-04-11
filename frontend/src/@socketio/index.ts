import { debounce, forIn, uniq } from "lodash";
import { io, Socket } from "socket.io-client";
import reduxStore from "../@redux/store";
import { getBaseUrl } from "../utilites";
import { log } from "../utilites/logger";
import { SocketIOReducer } from "./reducer";

class SocketIOClient {
  private socket: Socket;
  private events: SocketIO.Event[];
  private debounceReduce: () => void;

  private reducers: SocketIO.Reducer[];

  constructor() {
    const baseUrl = getBaseUrl();
    this.socket = io({
      path: `${baseUrl}/api/socket.io`,
      transports: ["websocket", "polling"],
    });

    this.socket.on("connect", this.onConnect.bind(this));
    this.socket.on("disconnect", this.onDisconnect.bind(this));
    this.socket.on("data", this.onEvent.bind(this));

    this.events = [];
    this.debounceReduce = debounce(this.reduce, 200);
    this.reducers = SocketIOReducer;
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

    forIn(records, (element, type) => {
      if (element) {
        const handlers = this.reducers.filter((v) => v.key === type);
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
            anyAction();
          }

          forIn(element, (ids, key) => {
            ids = uniq(ids);
            const action = handler[key as SocketIO.ActionType];
            if (action) {
              action();
            } else if (anyAction === undefined) {
              log("error", "Unhandle action of SocketIO event", key, type);
            }
          });
        });
      }
    });
  }

  private onConnect() {
    log("info", "Socket.IO has connected");
    this.onEvent({ type: "connect", action: "update", id: null });
  }

  private onDisconnect() {
    log("warning", "Socket.IO has disconnected");
    this.onEvent({ type: "disconnect", action: "update", id: null });
  }

  private onEvent(event: SocketIO.Event) {
    log("info", "Socket.IO receives", event);
    this.events.push(event);
    this.debounceReduce();
  }
}

export default new SocketIOClient();
