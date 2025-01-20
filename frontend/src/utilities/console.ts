/* eslint-disable no-console */
/* eslint-disable @typescript-eslint/no-explicit-any */

import { isProdEnv } from ".";

type LoggerType = "info" | "warning" | "error";

export function LOG(type: LoggerType, msg: string, ...payload: any[]) {
  if (import.meta.env.MODE === "test") {
    return;
  }

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

export function GROUP(
  header: string,
  content: (logger: typeof console.log) => void,
) {
  if (!isProdEnv) {
    console.group(header);
    content(console.log);
    console.groupEnd();
  }
}

// eslint-disable-next-line @typescript-eslint/no-empty-function
export const ASSERT = isProdEnv ? () => {} : console.assert;
