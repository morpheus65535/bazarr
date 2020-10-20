import { AxiosResponse } from "axios";
import apis from ".";

export default class SystemApi {
  get<T>(path: string, params?: any): Promise<AxiosResponse<T>> {
    return apis.axios.get(`/${path}`, { params });
  }

  postForm<T>(path: string, params?: any): Promise<AxiosResponse<T>> {
    let form = new FormData()

    for(const key in params) {
      form.append(key, params[key])
    }

    return apis.axios.post(`/${path}`, form);
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

  async status() {
    return new Promise<SystemStatusResult>((resolve, reject) => {
      this.get<DataWrapper<SystemStatusResult>>("systemstatus")
        .then((result) => {
          resolve(result.data.data);
        })
        .catch((reason) => {
          reject(reason);
        });
    });
  }

  async getTasks() {
    return new Promise<SystemTaskResult>((resolve, reject) => {
      this.get<DataWrapper<SystemTaskResult>>("systemtasks")
        .then((result) => {
          resolve(result.data.data);
        })
        .catch((reason) => {
          reject(reason);
        });
    });
  }

  async execTasks(id: string) {
    return new Promise<never>((resolve, reject) => {
      this.postForm<never>("systemtasks", { taskid: id })
        .then(() => {
          resolve();
        })
        .catch((reason) => {
          reject(reason);
        });
    });
  }
}
