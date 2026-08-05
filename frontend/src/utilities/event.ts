type CustomEventDetail<T> = T extends CustomEvent<infer D> ? D : never;

const createEvent = <
  K extends keyof WindowEventMap,
  P extends CustomEventDetail<WindowEventMap[K]>,
>(
  event: K,
  payload: P,
) => new CustomEvent<P>(event, { bubbles: true, detail: payload });

export const setAuthenticated = (authenticated: boolean) => {
  const event = createEvent("app-auth-changed", { authenticated });
  window.dispatchEvent(event);
};

export const setCriticalError = (message: string) => {
  const event = createEvent("app-critical-error", { message });

  window.dispatchEvent(event);
};

export const setOnlineStatus = (online: boolean) => {
  const event = createEvent("app-online-status", { online });
  window.dispatchEvent(event);
};
