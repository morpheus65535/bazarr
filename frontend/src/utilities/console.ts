/* eslint-disable no-console */
/* eslint-disable @typescript-eslint/no-explicit-any */

import { isProdEnv } from ".";

type LoggerType = "info" | "warning" | "error";

export function LOG(type: LoggerType, msg: string, ...payload: any[]) {
  if (!isProdEnv) {
    let logger = console.log;
    if (type === "warning") {
      logger = console.warn;
    } else if (type === "error") {
      logger = console.error;
    }
    logger(`[${type}] ${msg}`, ...payload);
  }
}

export function ENSURE(condition: boolean, msg: string, ...payload: any[]) {
  if (condition) {
    LOG("error", msg, payload);
  }
}

export const ASSERT = console.assert;
