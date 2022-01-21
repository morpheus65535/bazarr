import Axios, { AxiosError, AxiosInstance, CancelTokenSource } from "axios";
import { siteRedirectToAuth } from "../../@redux/actions";
import { AppDispatch } from "../../@redux/store";
import { Environment, isProdEnv } from "../../utilities";
class BazarrClient {
  axios!: AxiosInstance;
  source!: CancelTokenSource;
  dispatch!: AppDispatch;

  constructor() {
    const baseUrl = `${Environment.baseUrl}/api/`;
    this.initialize(baseUrl, Environment.apiKey);
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
        } else {
          error.message = "You have disconnected to Bazarr backend";
        }
        return Promise.reject(error);
      }
    );
  }

  _resetApi(apikey: string) {
    if (!isProdEnv) {
      this.axios.defaults.headers.common["X-API-KEY"] = apikey;
    }
  }

  handleError(code: number) {
    switch (code) {
      case 401:
        this.dispatch(siteRedirectToAuth());
        break;
      case 500:
        break;
      default:
        break;
    }
  }
}

export default new BazarrClient();
export * from "../hooks";
