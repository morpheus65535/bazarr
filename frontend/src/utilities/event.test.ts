import { describe, expect, it, vitest } from "vitest";
import {
  setAuthenticated,
  setCriticalError,
  setOnlineStatus,
} from "@/utilities/event";

describe("event utilities", () => {
  it("dispatches an app-auth-changed event", () => {
    const handler = vitest.fn();
    window.addEventListener("app-auth-changed", handler);

    setAuthenticated(true);

    expect(handler).toHaveBeenCalled();
    window.removeEventListener("app-auth-changed", handler);
  });

  it("dispatches an app-critical-error event", () => {
    const handler = vitest.fn();
    window.addEventListener("app-critical-error", handler);

    setCriticalError("something went wrong");

    expect(handler).toHaveBeenCalled();
    window.removeEventListener("app-critical-error", handler);
  });

  it("dispatches an app-online-status event", () => {
    const handler = vitest.fn();
    window.addEventListener("app-online-status", handler);

    setOnlineStatus(false);

    expect(handler).toHaveBeenCalled();
    window.removeEventListener("app-online-status", handler);
  });
});
