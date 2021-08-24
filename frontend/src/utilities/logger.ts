type LoggerType = "info" | "warning" | "error";

export function log(type: LoggerType, msg: string, ...payload: any[]) {
  if (process.env.NODE_ENV !== "production") {
    let logger = console.log;
    if (type === "warning") {
      logger = console.warn;
    } else if (type === "error") {
      logger = console.error;
    }
    logger(`[${type}] ${msg}`, ...payload);
  }
}

export function conditionalLog(
  condition: boolean,
  msg: string,
  ...payload: any[]
) {
  if (condition) {
    log("error", msg, payload);
  }
}
