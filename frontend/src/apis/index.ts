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

  private createFormdata(object?: LooseObject) {
    if (object) {
      let form = new FormData();

      for (const key in object) {
        const data = object[key];
        if (data instanceof Array) {
          if (data.length > 0) {
            data.forEach((val) => form.append(key, val));
          } else {
            form.append(key, "");
          }
        } else {
          form.append(key, object[key]);
        }
      }
      return form;
    } else {
      return undefined;
    }
  }

  post(path: string, formdata?: LooseObject, params?: LooseObject) {
    let form = this.createFormdata(formdata);

    return this.axios.post(path, form, { params });
  }

  patch(path: string, formdata?: LooseObject, params?: LooseObject) {
    let form = this.createFormdata(formdata);

    return this.axios.patch(path, form, { params });
  }

  delete(path: string, formdata?: LooseObject, params?: LooseObject) {
    let form = this.createFormdata(formdata);

    return this.axios.delete(path, { params, data: form });
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
export { default as ProvidersApi } from "./providers";
export { default as SubtitlesApi } from "./subtitles";
export { default as UtilsApi } from "./utils";
