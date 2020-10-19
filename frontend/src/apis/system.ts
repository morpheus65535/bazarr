import { AxiosResponse } from "axios";
import apis from ".";

export default class SystemApi {
  get<T>(path: string, params?: any): Promise<AxiosResponse<T>> {
    return apis.axios.get(`/${path}`, { params });
  }

  async shutdown() {
    return this.get<never>("shutdown");
  }

  async restart() {
    return this.get<never>("restart");
  }

  async languages(enabled: boolean = false) {
    return new Promise<Array<Language>>((resolve, reject) => {
      this.get<Array<Language>>("languages", { enabled })
        .then((result) => {
          resolve(result.data);
        })
        .catch((reason) => {
          reject(reason);
        });
    });
  }
}
