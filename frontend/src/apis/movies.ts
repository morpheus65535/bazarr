import { AxiosResponse } from "axios";
import apis from ".";

class MovieApi {
  get<T>(path: string, params?: any): Promise<AxiosResponse<T>> {
    return apis.axios.get(`/movies${path}`, { params });
  }

  postForm<T>(
    path: string,
    formdata?: any,
    params?: any
  ): Promise<AxiosResponse<T>> {
    return apis.post(`/movies${path}`, formdata, params);
  }

  patch(path: string, params?: any): Promise<void> {
    return apis.axios.patch(`/movies${path}`, { params });
  }

  async movies(id?: number): Promise<Array<Movie>> {
    return new Promise<Array<Movie>>((resolve, reject) => {
      this.get<DataWrapper<Array<Movie>>>("", { radarrid: id })
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
      this.postForm<void>("", { ...form }, { radarrid: id })
        .then(() => resolve())
        .catch((err) => reject(err));
    });
  }

  async wanted(): Promise<Array<WantedMovie>> {
    return new Promise<Array<WantedMovie>>((resolve, reject) => {
      this.get<DataWrapper<Array<WantedMovie>>>("/wanted")
        .then((result) => {
          resolve(result.data.data);
        })
        .catch((reason) => {
          reject(reason);
        });
    });
  }

  async history(id: number): Promise<Array<MovieHistory>> {
    return new Promise<Array<MovieHistory>>((resolve, reject) => {
      this.get<DataWrapper<Array<MovieHistory>>>("/history", {
        radarrid: id,
      })
        .then((result) => {
          resolve(result.data.data);
        })
        .catch((reason) => {
          reject(reason);
        });
    });
  }

  async scanDisk(id: number): Promise<void> {
    return this.patch("/disk");
  }

  async searchMissing(id: number): Promise<void> {
    return this.patch("/missing");
  }
}

export default new MovieApi();
