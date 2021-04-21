import Axios, { AxiosError, AxiosInstance, CancelTokenSource } from "axios";
import { siteRedirectToAuth, siteUpdateOffline } from "../@redux/actions";
import reduxStore from "../@redux/store";
class Api {
  axios!: AxiosInstance;
  source!: CancelTokenSource;

  constructor() {
    if (process.env.NODE_ENV === "development") {
      this.initialize("/api/", process.env["REACT_APP_APIKEY"]!);
    } else {
      const baseUrl =
        window.Bazarr.baseUrl === "/"
          ? "/api/"
          : `${window.Bazarr.baseUrl}/api/`;
      this.initialize(baseUrl, window.Bazarr.apiKey);
    }
  }

  initialize(url: string, apikey?: string) {
    this.axios = Axios.create({
      baseURL: url,
    });

    this.axios.defaults.headers.post["Content-Type"] = "application/json";
    this.axios.defaults.headers.common["X-API-KEY"] = apikey ?? "AUTH_NEEDED";

    this.source = Axios.CancelToken.source();

    this.axios.interceptors.request.use((config) => {
      config.cancelToken = this.source.token;
      return config;
    });

    this.axios.interceptors.response.use(
      (resp) => {
        this.onOnline();
        if (resp.status >= 200 && resp.status < 300) {
          return Promise.resolve(resp);
        } else {
          this.handleError(resp.status);
          return Promise.reject(resp);
        }
      },
      (error: AxiosError) => {
        if (error.response) {
          const response = error.response;
          this.handleError(response.status);
          this.onOnline();
        } else {
          this.onOffline();
          error.message = "You have disconnected to Bazarr backend";
        }
        return Promise.reject(error);
      }
    );
  }

  danger_resetApi(apikey: string) {
    this.axios.defaults.headers.common["X-API-KEY"] = apikey;
  }

  onOnline() {
    const offline = reduxStore.getState().site.offline;
    if (offline) {
      reduxStore.dispatch(siteUpdateOffline(false));
    }
  }

  onOffline() {
    reduxStore.dispatch(siteUpdateOffline(true));
  }

  handleError(code: number) {
    switch (code) {
      case 401:
        reduxStore.dispatch(siteRedirectToAuth());
        break;
      case 500:
        break;
      default:
        break;
    }
  }
}

export default new Api();
export { default as BadgesApi } from "./badges";
export { default as EpisodesApi } from "./episodes";
export { default as FilesApi } from "./files";
export { default as HistoryApi } from "./history";
export { default as MoviesApi } from "./movies";
export { default as ProvidersApi } from "./providers";
export { default as SeriesApi } from "./series";
export { default as SubtitlesApi } from "./subtitles";
export { default as SystemApi } from "./system";
export { default as UtilsApi } from "./utils";
