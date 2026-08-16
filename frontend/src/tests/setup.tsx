import { http } from "msw";
import { HttpResponse } from "msw";
import { vi, vitest } from "vitest";
import "@testing-library/jest-dom";
import queryClient from "@/apis/queries";
import server from "./mocks/node";

vi.mock("recharts", () => ({
  ResponsiveContainer: ({ children }: { children: React.ReactNode }) => (
    <div style={{ width: "100%", height: "100%" }}>{children}</div>
  ),
  BarChart: () => null,
  Bar: () => null,
  XAxis: () => null,
  YAxis: () => null,
  CartesianGrid: () => null,
  Tooltip: () => null,
  Legend: () => null,
  Cell: vi.fn(),
}));

if (typeof window !== "undefined") {
  Object.defineProperty(window, "matchMedia", {
    writable: true,
    value: vitest.fn().mockImplementation((query) => ({
      matches: false,
      media: query,
      onchange: null,
      addListener: vitest.fn(),
      removeListener: vitest.fn(),
      addEventListener: vitest.fn(),
      removeEventListener: vitest.fn(),
      dispatchEvent: vitest.fn(),
    })),
  });

  class ResizeObserver {
    observe() {
      return undefined;
    }
    unobserve() {
      return undefined;
    }
    disconnect() {
      return undefined;
    }
  }

  window.ResizeObserver = ResizeObserver;

  class IntersectionObserver {
    observe() {
      return undefined;
    }
    unobserve() {
      return undefined;
    }
    disconnect() {
      return undefined;
    }
  }

  window.IntersectionObserver =
    IntersectionObserver as unknown as typeof window.IntersectionObserver;

  window.scrollTo = () => undefined;

  const localStorageMock = (() => {
    const store: Record<string, string> = {};
    return {
      getItem: vi.fn((key: string) => store[key] ?? null),
      setItem: vi.fn((key: string, value: string) => {
        store[key] = value;
      }),
      removeItem: vi.fn((key: string) => {
        delete store[key];
      }),
      clear: vi.fn(() => {
        Object.keys(store).forEach((key) => delete store[key]);
      }),
    };
  })();

  Object.defineProperty(window, "localStorage", {
    value: localStorageMock,
  });
}

beforeAll(() => {
  server.listen({ onUnhandledRequest: "error" });
});

beforeEach(() => {
  server.resetHandlers();
  server.use(
    http.get("/api/system/settings", () => {
      return HttpResponse.json({
        general: {
          theme: "auto",
        },
      });
    }),
    http.get("/api/system/languages", () => {
      return HttpResponse.json([]);
    }),
    http.get("/api/system/languages/profiles", () => {
      return HttpResponse.json([]);
    }),
  );
});

afterEach(() => {
  server.resetHandlers();
  queryClient.clear();
});

afterAll(() => server.close());
