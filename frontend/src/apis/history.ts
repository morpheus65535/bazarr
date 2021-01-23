import { AxiosResponse } from "axios";
import apis from ".";

class HistoryApi {
  get<T>(path: string, params?: any): Promise<AxiosResponse<T>> {
    return apis.axios.get(`/history${path}`, { params });
  }

  async movies(): Promise<Array<MovieHistory>> {
    return new Promise<Array<MovieHistory>>((resolve, reject) => {
      this.get<DataWrapper<Array<MovieHistory>>>("/movies")
        .then((result) => {
          resolve(result.data.data);
        })
        .catch((reason) => {
          reject(reason);
        });
    });
  }

  async series(): Promise<Array<SeriesHistory>> {
    return new Promise<Array<SeriesHistory>>((resolve, reject) => {
      this.get<DataWrapper<Array<SeriesHistory>>>("/series")
        .then((result) => {
          resolve(result.data.data);
        })
        .catch((reason) => {
          reject(reason);
        });
    });
  }
}

export default new HistoryApi();
