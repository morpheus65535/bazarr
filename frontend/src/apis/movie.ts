import { AxiosResponse } from "axios";
import apis from ".";

export default class MovieApi {
  get<T>(path: string, params?: any): Promise<AxiosResponse<T>> {
    return apis.axios.get(`/movies${path}`, { params });
  }

  postForm<T>(
    path: string,
    formdata?: any,
    params?: any
  ): Promise<AxiosResponse<T>> {
    let form = new FormData();

    for (const key in formdata) {
      form.append(key, formdata[key]);
    }

    return apis.axios.post(`/movies${path}`, form, { params });
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
}
