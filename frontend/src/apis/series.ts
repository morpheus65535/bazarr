import { AxiosResponse } from "axios";
import apis from ".";

export default class SeriesApi {
  get<T>(path: string, params?: any): Promise<AxiosResponse<T>> {
    return apis.axios.get(`/${path}`, { params });
  }

  postForm<T>(path: string, params?: any): Promise<AxiosResponse<T>> {
    let form = new FormData();

    for (const key in params) {
      form.append(key, params[key]);
    }

    return apis.axios.post(`/${path}`, form);
  }

  async series(): Promise<Array<Series>> {
    return new Promise<Array<Series>>((resolve, reject) => {
      this.get<DataWrapper<Array<Series>>>("series")
        .then((result) => {
          resolve(result.data.data);
        })
        .catch((reason) => {
          reject(reason);
        });
    });
  }

  async wanted(
    draw: number,
    start: number,
    length: number
  ): Promise<Array<WantedSeries>> {
    return new Promise<Array<WantedSeries>>((resolve, reject) => {
      this.get<DataWrapper<Array<WantedSeries>>>("wanted_series", {
        draw,
        start,
        length,
      })
        .then((result) => {
          resolve(result.data.data);
        })
        .catch((reason) => {
          reject(reason);
        });
    });
  }

  async search(): Promise<never> {
    return new Promise<never>((resolve, reject) => {
      this.get<never>("search_wanted_series")
        .then((result) => {
          resolve();
        })
        .catch((reason) => {
          reject(reason);
        });
    });
  }

  async download(request: SeriesSubDownloadRequest): Promise<never> {
    return new Promise<never>((resolve, reject) => {
      this.postForm<never>("episodes_subtitles_download", request)
        .then((result) => {
          resolve();
        })
        .catch((reason) => {
          reject(reason);
        });
    });
  }
}
