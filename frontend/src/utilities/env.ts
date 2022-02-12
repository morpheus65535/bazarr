export const isDevEnv = process.env.NODE_ENV === "development";
export const isProdEnv = process.env.NODE_ENV === "production";
export const isTestEnv = process.env.NODE_ENV === "test";

export const Environment = {
  get apiKey(): string | undefined {
    if (isDevEnv) {
      return process.env["REACT_APP_APIKEY"]!;
    } else if (isTestEnv) {
      return undefined;
    } else {
      return window.Bazarr.apiKey;
    }
  },
  get canUpdate(): boolean {
    if (isDevEnv) {
      return process.env["REACT_APP_CAN_UPDATE"] === "true";
    } else if (isTestEnv) {
      return false;
    } else {
      return window.Bazarr.canUpdate;
    }
  },
  get hasUpdate(): boolean {
    if (isDevEnv) {
      return process.env["REACT_APP_HAS_UPDATE"] === "true";
    } else if (isTestEnv) {
      return false;
    } else {
      return window.Bazarr.hasUpdate;
    }
  },
  get baseUrl(): string {
    if (isDevEnv || isTestEnv) {
      // TODO: Support overriding base URL in development env
      return "";
    } else {
      let url = window.Bazarr.baseUrl;
      if (url.endsWith("/")) {
        url = url.slice(0, -1);
      }
      return url;
    }
  },
  get queryDev(): boolean {
    if (isDevEnv) {
      return process.env["REACT_APP_QUERY_DEV"] === "true";
    }
    return false;
  },
};
