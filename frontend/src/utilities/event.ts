type CustomEventDetail<T> = T extends CustomEvent<infer D> ? D : never;

function createEvent<
  K extends keyof WindowEventMap,
  P extends CustomEventDetail<WindowEventMap[K]>
>(event: K, payload: P) {
  return new CustomEvent<P>(event, { bubbles: true, detail: payload });
}

export function setLoginRequired() {
  const event = createEvent("app-login-required", {});
  window.dispatchEvent(event);
}

export function setCriticalError(message: string) {
  const event = createEvent("app-critical-error", { message });

  window.dispatchEvent(event);
}

export function setOnlineStatus(online: boolean) {
  const event = createEvent("app-online-status", { online });
  window.dispatchEvent(event);
}
