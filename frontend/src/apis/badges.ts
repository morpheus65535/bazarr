import { AxiosResponse } from "axios";
import apis from ".";

export default class BadgesApi {
  get<T>(path: string, params?: any): Promise<AxiosResponse<T>> {
    return apis.axios.get(`/badges/${path}`, { params });
  }

  async series(): Promise<number> {
    return new Promise<number>((resolve, reject) => {
      this.get<SeriesBadge>("series")
        .then((result) => {
          resolve(result.data.missing_episodes);
        })
        .catch((reason) => {
          reject(reason);
        });
    });
  }

  async movies(): Promise<number> {
    return new Promise<number>((resolve, reject) => {
      this.get<MoviesBadge>("movies")
        .then((result) => {
          resolve(result.data.missing_movies);
        })
        .catch((reason) => {
          reject(reason);
        });
    });
  }

  async providers(): Promise<number> {
    return new Promise<number>((resolve, reject) => {
      this.get<ProvidersBadge>("providers")
        .then((result) => {
          resolve(result.data.throttled_providers);
        })
        .catch((reason) => {
          reject(reason);
        });
    });
  }
}
