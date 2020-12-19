import Axios, { AxiosInstance, CancelTokenSource } from "axios";
class Api {
  axios!: AxiosInstance;
  source!: CancelTokenSource;

  constructor() {
    if (process.env.NODE_ENV === "development") {
      this.recreateAxios("/api/", process.env.REACT_APP_APIKEY!);
    } else {
      const baseUrl =
        window.Bazarr.baseUrl === "/"
          ? "/api/"
          : `${window.Bazarr.baseUrl}/api/`;
      this.recreateAxios(baseUrl, window.Bazarr.apiKey);
    }
  }

  post(path: string, formdata?: any, params?: any) {
    let form = new FormData();

    for (const key in formdata) {
      const data = formdata[key];
      if (data instanceof Array) {
        data.forEach((val) => form.append(key, val));
      } else {
        form.append(key, formdata[key]);
      }
    }

    return this.axios.post(path, form, { params });
  }

  recreateAxios(url: string, apikey: string) {
    this.axios = Axios.create({
      baseURL: url,
    });

    this.axios.defaults.headers.post["Content-Type"] = "application/json";
    this.axios.defaults.headers.common["x-api-key"] = apikey;

    this.source = Axios.CancelToken.source();

    this.axios.interceptors.request.use((config) => {
      config.cancelToken = this.source.token;
      return config;
    });
  }

  handle5xxRequest() {}

  handle4xxRequest() {}

  cancelAllRequest() {}
}

export default new Api();
export { default as BadgesApi } from "./badges";
export { default as SystemApi } from "./system";
export { default as SeriesApi } from "./series";
export { default as MoviesApi } from "./movies";
export { default as HistoryApi } from "./history";
export { default as EpisodesApi } from "./episodes";
