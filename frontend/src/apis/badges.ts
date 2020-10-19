import { AxiosResponse } from "axios";
import apis from ".";

export default class BadgesApi {
  get<T>(path: string, params?: any): Promise<AxiosResponse<T>> {
    return apis.axios.get(`/${path}`, { params });
  }

  async series(): Promise<number> {
    return new Promise<number>((resolve, reject) => {
      this.get<SeriesBadge>("badges_series")
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
      this.get<MoviesBadge>("badges_movies")
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
      this.get<ProvidersBadge>("badges_providers")
        .then((result) => {
          resolve(result.data.throttled_providers);
        })
        .catch((reason) => {
          reject(reason);
        });
    });
  }
}
