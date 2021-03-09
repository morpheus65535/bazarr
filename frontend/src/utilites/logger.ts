type LoggerType = "info" | "warning" | "error";

export function log(type: LoggerType, msg: string, ...payload: any[]) {
  if (process.env.NODE_ENV !== "production") {
    console.log(`[${type}] ${msg}`, ...payload);
  }
}
