import { beforeEach, describe, expect, it, vi } from "vitest";
import { Environment, isDevEnv, isProdEnv, isTestEnv } from "@/utilities/env";

describe("env utilities", () => {
  describe("static test environment", () => {
    it("reports the correct environment flags", () => {
      expect(isTestEnv).toBe(true);
      expect(isDevEnv).toBe(false);
      expect(isProdEnv).toBe(false);
    });

    it("returns test environment values", () => {
      expect(Environment.apiKey).toBeUndefined();
      expect(Environment.canUpdate).toBe(false);
      expect(Environment.hasUpdate).toBe(false);
      expect(Environment.baseUrl).toBe("");
      expect(Environment.queryDev).toBe(false);
    });
  });

  describe("dynamic environment imports", () => {
    beforeEach(() => {
      vi.resetModules();
    });

    it("reads VITE_* values in development mode", async () => {
      const env = import.meta.env as Record<string, string | undefined>;
      env.MODE = "development";
      env.VITE_API_KEY = "dev-key";
      env.VITE_CAN_UPDATE = "true";
      env.VITE_HAS_UPDATE = "true";
      env.VITE_QUERY_DEV = "true";

      const { Environment: dynamicEnv } = await import("@/utilities/env");

      expect(dynamicEnv.apiKey).toBe("dev-key");
      expect(dynamicEnv.canUpdate).toBe(true);
      expect(dynamicEnv.hasUpdate).toBe(true);
      expect(dynamicEnv.baseUrl).toBe("");
      expect(dynamicEnv.queryDev).toBe(true);
    });

    it("reads window.Bazarr values in production mode", async () => {
      const env = import.meta.env as Record<string, string | undefined>;
      env.MODE = "production";
      window.Bazarr = {
        baseUrl: "/bazarr/",
        apiKey: "prod-key",
        canUpdate: true,
        hasUpdate: true,
      };

      const { Environment: dynamicEnv } = await import("@/utilities/env");

      expect(dynamicEnv.apiKey).toBe("prod-key");
      expect(dynamicEnv.canUpdate).toBe(true);
      expect(dynamicEnv.hasUpdate).toBe(true);
      expect(dynamicEnv.baseUrl).toBe("/bazarr");
    });

    it("trims a trailing slash from the production baseUrl", async () => {
      const env = import.meta.env as Record<string, string | undefined>;
      env.MODE = "production";
      window.Bazarr = {
        baseUrl: "/bazarr",
        apiKey: undefined,
        canUpdate: false,
        hasUpdate: false,
      };

      const { Environment: dynamicEnv } = await import("@/utilities/env");

      expect(dynamicEnv.baseUrl).toBe("/bazarr");
    });
  });
});
