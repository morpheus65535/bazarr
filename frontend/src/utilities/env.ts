export const isDevEnv = import.meta.env.MODE === "development";
export const isProdEnv = import.meta.env.MODE === "production";
export const isTestEnv = import.meta.env.MODE === "test";

const readEnv = <T>(devValue: T, testValue: T, prodValue: () => T): T => {
  if (isDevEnv) {
    return devValue;
  }
  if (isTestEnv) {
    return testValue;
  }
  return prodValue();
};

export const Environment = {
  get apiKey(): string | undefined {
    return readEnv(import.meta.env.VITE_API_KEY, undefined, () => {
      return window.Bazarr.apiKey;
    });
  },
  get canUpdate(): boolean {
    return readEnv(
      import.meta.env.VITE_CAN_UPDATE === "true",
      false,
      () => window.Bazarr.canUpdate,
    );
  },
  get hasUpdate(): boolean {
    return readEnv(
      import.meta.env.VITE_HAS_UPDATE === "true",
      false,
      () => window.Bazarr.hasUpdate,
    );
  },
  get isConfigured(): boolean {
    return readEnv(
      import.meta.env.VITE_IS_CONFIGURED === "true",
      false,
      () => window.Bazarr.isConfigured,
    );
  },
  get baseUrl(): string {
    if (isDevEnv || isTestEnv) {
      return "";
    }
    const url = window.Bazarr.baseUrl;
    return url.endsWith("/") ? url.slice(0, -1) : url;
  },
  get queryDev(): boolean {
    return isDevEnv && import.meta.env.VITE_QUERY_DEV === "true";
  },
  get isOnboardingForced(): boolean {
    return isDevEnv && import.meta.env.VITE_FORCE_ONBOARDING === "true";
  },
};
