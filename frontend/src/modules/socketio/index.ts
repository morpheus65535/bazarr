import { onlineManager } from "@tanstack/react-query";
import { debounce, forIn, remove, uniq } from "lodash";
import { io, Socket } from "socket.io-client";
import { Environment, isDevEnv, isTestEnv } from "@/utilities";
import { ENSURE, GROUP, LOG } from "@/utilities/console";
import { createDefaultReducer } from "./reducer";

class SocketIOClient {
  private socket: Socket;
  private events: SocketIO.Event[];
  private debounceReduce: () => void;

  private reducers: SocketIO.Reducer[];

  constructor() {
    this.socket = io({
      path: `${Environment.baseUrl}/api/socket.io`,
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
    this.debounceReduce = debounce(this.reduce, 3);
    this.reducers = [];

    onlineManager.setOnline(false);

    if (isDevEnv) {
      window.socketIO = {
        dump: () => {
          GROUP("Socket.IO Reducers", (logger) => {
            this.reducers.forEach((reducer) => {
              logger(reducer.key);
            });
          });
        },
        emit: (e) => {
          if (e) {
            this.onEvent(e);
          }
        },
      };
    }
  }

  initialize() {
    if (isTestEnv) {
      return;
    }

    LOG("info", "Initializing Socket.IO client...");
    this.reducers.push(...createDefaultReducer());

    window.addEventListener("app-auth-changed", (ev) => {
      const authenticated = ev.detail.authenticated;
      LOG("info", "Authentication status change to", authenticated);
      if (authenticated) {
        this.connect();
      } else {
        this.disconnect();
      }
    });
  }

  connect() {
    LOG("info", "Connecting Socket.IO client...");
    this.socket.connect();
  }

  disconnect() {
    LOG("info", "Disconnecting Socket.IO client...");
    this.socket.disconnect();
  }

  addReducer(reducer: SocketIO.Reducer) {
    this.reducers.push(reducer);
  }

  removeReducer(reducer: SocketIO.Reducer) {
    const removed = remove(this.reducers, (r) => r === reducer);
    ENSURE(removed.length === 0, "Fail to remove reducer", reducer);
  }

  private reduce() {
    const events = [...this.events];
    this.events = [];

    const records: SocketIO.ActionRecord = {};

    events.forEach((e) => {
      if (!(e.type in records)) {
        records[e.type] = {};
      }

      const record = records[e.type];
      if (record === undefined) {
        return;
      }

      if (!(e.action in record)) {
        record[e.action] = [];
      }

      if (e.payload) {
        record[e.action]?.push(e.payload);
      }
    });

    forIn(records, (element, type) => {
      if (element) {
        const handlers = this.reducers.filter((v) => v.key === type);
        if (handlers.length === 0) {
          LOG("warning", "Unhandled SocketIO event", type);
          return;
        }

        handlers.forEach((handler) => {
          const anyAction = handler.any;
          if (anyAction) {
            anyAction();
          }

          forIn(element, (ids, key) => {
            ids = uniq(ids);
            const action = handler[key as SocketIO.ActionType];
            if (action) {
              // FIXME: type
              // eslint-disable-next-line @typescript-eslint/no-explicit-any
              action(ids as any[]);
            } else if (anyAction === undefined) {
              LOG("warning", "Unhandled SocketIO event", key, type);
            }
          });
        });
      }
    });
  }

  private onConnect() {
    LOG("info", "Socket.IO has connected");
    onlineManager.setOnline(true);
    this.onEvent({ type: "connect", action: "update" });
  }

  private onConnectError() {
    LOG("warning", "Socket.IO has error connecting backend");
    onlineManager.setOnline(false);
    this.onEvent({ type: "connect_error", action: "update" });
  }

  private onDisconnect() {
    LOG("warning", "Socket.IO has disconnected");
    onlineManager.setOnline(false);
    this.onEvent({ type: "disconnect", action: "update" });
  }

  private onEvent(event: SocketIO.Event) {
    LOG("info", "Socket.IO receives", event);
    this.events.push(event);
    this.debounceReduce();
  }
}

const socketIOClient = new SocketIOClient();

export default socketIOClient;
