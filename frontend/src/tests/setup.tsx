/* eslint-disable @typescript-eslint/no-empty-function */

import { http } from "msw";
import { HttpResponse } from "msw";
import { vi, vitest } from "vitest";
import "@testing-library/jest-dom";
import server from "./mocks/node";

vi.mock("recharts", async () => {
  const OriginalRechartsModule = await vi.importActual("recharts");

  return {
    ...OriginalRechartsModule,
    ResponsiveContainer: ({ children }: { children: React.ReactNode }) => (
      <div style={{ width: "100%", height: "100%" }}>{children}</div>
    ),
  };
});

// From https://stackoverflow.com/questions/39830580/jest-test-fails-typeerror-window-matchmedia-is-not-a-function
Object.defineProperty(window, "matchMedia", {
  writable: true,
  value: vitest.fn().mockImplementation((query) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vitest.fn(), // Deprecated
    removeListener: vitest.fn(), // Deprecated
    addEventListener: vitest.fn(),
    removeEventListener: vitest.fn(),
    dispatchEvent: vitest.fn(),
  })),
});

// From https://github.com/mantinedev/mantine/blob/master/configuration/jest/jsdom.mocks.js
class ResizeObserver {
  observe() {}
  unobserve() {}
  disconnect() {}
}

window.ResizeObserver = ResizeObserver;

window.scrollTo = () => {};

beforeAll(() => {
  server.listen({ onUnhandledRequest: "error" });

  server.use(
    http.get("/api/system/settings", () => {
      return HttpResponse.json({
        general: {
          theme: "auto",
        },
      });
    }),
  );
});

afterEach(() => server.resetHandlers());

afterAll(() => server.close());
