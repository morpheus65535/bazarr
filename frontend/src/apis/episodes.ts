import { AxiosResponse } from "axios"
import apis from "."

export default class EpisodeApi {
  get<T>(path: string, params?: any): Promise<AxiosResponse<T>> {
    return apis.axios.get(`/episodes${path}`, { params });
  }

  async all(seriesid: number): Promise<Array<Episode>> {
    return new Promise<Array<Episode>>((resolve, reject) => {
      this.get<DataWrapper<Array<Episode>>>("", { seriesid })
        .then((result) => {
          resolve(result.data.data);
        })
        .catch((reason) => {
          reject(reason);
        });
    });
  }
}