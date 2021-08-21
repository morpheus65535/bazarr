import { debounce, forIn, remove, uniq } from "lodash";
import { io, Socket } from "socket.io-client";
import { getBaseUrl } from "../../utilites";
import { conditionalLog, log } from "../../utilites/logger";
import { createDefaultReducer } from "./reducer";

class SocketIOClient {
  private socket: Socket;
  private events: SocketIO.Event[];
  private debounceReduce: () => void;

  private reducers: SocketIO.Reducer[];

  constructor() {
    const baseUrl = getBaseUrl();
    this.socket = io({
      path: `${baseUrl}/api/socket.io`,
      transports: ["polling", "websocket"],
      upgrade: true,
      rememberUpgrade: true,
      autoConnect: false,
    });

    this.socket.on("connect", this.onConnect.bind(this));
    this.socket.on("disconnect", this.onDisconnect.bind(this));
    this.socket.on("connect_error", this.onConnectError.bind(this));
    this.socket.on("data", this.onEvent.bind(this));

    this.events = [];
    this.debounceReduce = debounce(this.reduce, 20);
    this.reducers = [];
  }

  initialize() {
    this.reducers.push(...createDefaultReducer());
    this.socket.connect();

    // Debug Command
    window._socketio = {
      dump: this.dump.bind(this),
      emit: this.onEvent.bind(this),
    };
  }

  private dump() {
    console.log("SocketIO reducers", this.reducers);
  }

  addReducer(reducer: SocketIO.Reducer) {
    this.reducers.push(reducer);
  }

  removeReducer(reducer: SocketIO.Reducer) {
    const removed = remove(this.reducers, (r) => r === reducer);
    conditionalLog(removed.length === 0, "Fail to remove reducer", reducer);
  }

  private reduce() {
    const events = [...this.events];
    this.events = [];

    const records: SocketIO.ActionRecord = {};

    events.forEach((e) => {
      if (!(e.type in records)) {
        records[e.type] = {};
      }

      const record = records[e.type]!;
      if (!(e.action in record)) {
        record[e.action] = [];
      }
      if (e.payload) {
        record[e.action]!.push(e.payload);
      }
    });

    forIn(records, (element, type) => {
      if (element) {
        const handlers = this.reducers.filter((v) => v.key === type);
        if (handlers.length === 0) {
          log("warning", "Unhandle SocketIO event", type);
          return;
        }

        // eslint-disable-next-line no-loop-func
        handlers.forEach((handler) => {
          const anyAction = handler.any;
          if (anyAction) {
            anyAction();
          }

          forIn(element, (ids, key) => {
            ids = uniq(ids);
            const action = handler[key as SocketIO.ActionType];
            if (action) {
              action(ids);
            } else if (anyAction === undefined) {
              log("warning", "Unhandled SocketIO event", key, type);
            }
          });
        });
      }
    });
  }

  private onConnect() {
    log("info", "Socket.IO has connected");
    this.onEvent({ type: "connect", action: "update", payload: null });
  }

  private onConnectError() {
    log("warning", "Socket.IO has error connecting backend");
    this.onEvent({ type: "connect_error", action: "update", payload: null });
  }

  private onDisconnect() {
    log("warning", "Socket.IO has disconnected");
    this.onEvent({ type: "disconnect", action: "update", payload: null });
  }

  private onEvent(event: SocketIO.Event) {
    log("info", "Socket.IO receives", event);
    this.events.push(event);
    this.debounceReduce();
  }
}

export default new SocketIOClient();
