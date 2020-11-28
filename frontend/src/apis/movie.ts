import { AxiosResponse } from "axios";
import apis from ".";

export default class MovieApi {
  get<T>(path: string, params?: any): Promise<AxiosResponse<T>> {
    return apis.axios.get(`/${path}`, { params });
  }

  async movies(): Promise<Array<Movie>> {
    return new Promise<Array<Movie>>((resolve, reject) => {
      this.get<DataWrapper<Array<Movie>>>("movies")
        .then((result) => {
          resolve(result.data.data);
        })
        .catch((reason) => {
          reject(reason);
        });
    });
  }
}
