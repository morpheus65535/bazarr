import Axios, { AxiosInstance } from "axios";

type UrlTestResponse =
  | {
      status: true;
      version: string;
    }
  | {
      status: false;
      error: string;
    };

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

  urlTest(
    protocol: string,
    url: string,
    params?: any
  ): Promise<UrlTestResponse> {
    return new Promise<UrlTestResponse>((resolve, reject) => {
      this.axios
        .get(`test/${protocol}/${url}api/system/status`, { params })
        .then((result) => resolve(result.data))
        .catch(reject);
    });
  }
}

export default new RequestUtils();
