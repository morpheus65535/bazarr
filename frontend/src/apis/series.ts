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

  patch<T>(path: string, form?: any, params?: any): Promise<AxiosResponse<T>> {
    return apis.patch(`/series${path}`, form, params);
  }

  delete<T>(path: string, form?: any, params?: any): Promise<AxiosResponse<T>> {
    return apis.delete(`/series${path}`, form, params);
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

  async scanDisk(id: number): Promise<void> {
    return new Promise<void>((resolve, reject) => {
      this.patch("/disk", undefined, { radarrid: id })
        .then(() => resolve())
        .catch(reject);
    });
  }

  async searchMissing(id: number): Promise<void> {
    return new Promise<void>((resolve, reject) => {
      this.patch("/missing", undefined, { radarrid: id })
        .then(() => resolve())
        .catch(reject);
    });
  }
}

export default new SeriesApi();
