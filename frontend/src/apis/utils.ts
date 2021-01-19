import Axios, { AxiosInstance, AxiosResponse } from "axios";
import { result } from "lodash";

class RequestUtils {
  private axios!: AxiosInstance;

  constructor() {
    if (process.env.NODE_ENV === "development") {
      this.recreateAxios("/", process.env.REACT_APP_APIKEY!);
    } else {
      const baseUrl =
        window.Bazarr.baseUrl === "/" ? "/" : `${window.Bazarr.baseUrl}/`;
      this.recreateAxios(baseUrl, window.Bazarr.apiKey);
    }
  }

  private recreateAxios(url: string, apikey: string) {
    this.axios = Axios.create({
      baseURL: url,
    });

    this.axios.defaults.headers.post["Content-Type"] = "application/json";
    this.axios.defaults.headers.common["x-api-key"] = apikey;
  }

  urlTest<T>(protocol: string, url: string, params?: any): Promise<T> {
    return new Promise<T>((resolve, reject) => {
      this.axios
        .get(`test/${protocol}/${url}api/system/status`, { params })
        .then((result) => resolve(result.data))
        .catch(reject);
    });
  }
}

export default new RequestUtils();
