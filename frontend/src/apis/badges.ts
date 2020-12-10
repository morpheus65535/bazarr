import { AxiosResponse } from "axios";
import apis from ".";

export default class BadgesApi {
  get<T>(path: string, params?: any): Promise<AxiosResponse<T>> {
    return apis.axios.get(`/badges/${path}`, { params });
  }

  async series(): Promise<number> {
    return new Promise<number>((resolve, reject) => {
      this.get<Badge>("series")
        .then((result) => {
          resolve(result.data.value);
        })
        .catch((reason) => {
          reject(reason);
        });
    });
  }

  async movies(): Promise<number> {
    return new Promise<number>((resolve, reject) => {
      this.get<Badge>("movies")
        .then((result) => {
          resolve(result.data.value);
        })
        .catch((reason) => {
          reject(reason);
        });
    });
  }

  async providers(): Promise<number> {
    return new Promise<number>((resolve, reject) => {
      this.get<Badge>("providers")
        .then((result) => {
          resolve(result.data.value);
        })
        .catch((reason) => {
          reject(reason);
        });
    });
  }
}
