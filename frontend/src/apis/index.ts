import Axios, { AxiosInstance, CancelTokenSource } from "axios";
import BadgesApi from "./badges";
import SystemApi from "./system";
import SeriesApi from "./series";

class Api {
  axios!: AxiosInstance;
  source!: CancelTokenSource;

  system: SystemApi = new SystemApi();
  badges: BadgesApi = new BadgesApi();
  series: SeriesApi = new SeriesApi();

  constructor() {
    if (process.env.NODE_ENV === "development") {
      this.recreateAxios("api/", process.env.REACT_APP_APIKEY!);
    } else {
      this.recreateAxios("api/", window.Bazarr.apikey);
    }
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
