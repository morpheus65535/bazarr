import { AxiosResponse } from "axios";
import apis from ".";

class SeriesApi {
  get<T>(path: string, params?: any): Promise<AxiosResponse<T>> {
    return apis.axios.get(`/series${path}`, { params });
  }

  postForm<T>(
    path: string,
    formdata?: any,
    params?: any
  ): Promise<AxiosResponse<T>> {
    return apis.post(`/series${path}`, formdata, params);
  }

  async series(id?: number): Promise<Array<Series>> {
    return new Promise<Array<Series>>((resolve, reject) => {
      this.get<DataWrapper<Array<Series>>>("", { seriesid: id })
        .then((result) => {
          resolve(result.data.data);
        })
        .catch((reason) => {
          reject(reason);
        });
    });
  }

  async modify(id: number, form: ItemModifyForm) {
    return new Promise<void>((resolve, reject) => {
      this.postForm<void>("", { ...form }, { seriesid: id })
        .then(() => resolve())
        .catch((err) => reject(err));
    });
  }

  async wanted(): Promise<Array<WantedEpisode>> {
    return new Promise<Array<WantedEpisode>>((resolve, reject) => {
      this.get<DataWrapper<Array<WantedEpisode>>>("/wanted")
        .then((result) => {
          resolve(result.data.data);
        })
        .catch((reason) => {
          reject(reason);
        });
    });
  }

  async search(): Promise<void> {
    return new Promise<void>((resolve, reject) => {
      this.get<void>("search_wanted_series")
        .then(() => {
          resolve();
        })
        .catch((err) => {
          reject(err);
        });
    });
  }

  async download(form: SeriesDownloadForm): Promise<void> {
    return new Promise<void>((resolve, reject) => {
      this.postForm<void>("episodes_subtitles_download", form)
        .then(() => {
          resolve();
        })
        .catch((err) => {
          reject(err);
        });
    });
  }
}

export default new SeriesApi()