import { AxiosResponse } from "axios";
import apis from ".";

class SystemApi {
  private get<T>(path: string, params?: any): Promise<AxiosResponse<T>> {
    return apis.axios.get(`/system${path}`, { params });
  }

  private postForm<T>(
    path: string,
    formdata?: any,
    params?: any
  ): Promise<AxiosResponse<T>> {
    return apis.post(`/system${path}`, formdata, params);
  }

  private delete<T>(path: string, params?: any): Promise<AxiosResponse<T>> {
    return apis.axios.delete(`/system${path}`, { params });
  }

  async performAction(action: string) {
    return this.postForm<void>("", undefined, { action });
  }

  async shutdown() {
    return this.performAction("shutdown");
  }

  async restart() {
    return this.performAction("restart");
  }

  async settings() {
    return new Promise<SystemSettings>((resolve, reject) => {
      this.get<SystemSettings>("/settings")
        .then((result) => {
          resolve(result.data);
        })
        .catch(reject);
    });
  }

  async setSettings(data: object) {
    return new Promise<void>((resolve, reject) => {
      this.postForm<void>("/settings", data)
        .then((res) => {
          resolve();
        })
        .catch(reject);
    });
  }

  async languages(enabled: boolean) {
    return new Promise<Array<Language>>((resolve, reject) => {
      this.get<Array<Language>>("/languages", { enabled })
        .then((result) => {
          resolve(result.data);
        })
        .catch((reason) => {
          reject(reason);
        });
    });
  }

  async languagesProfileList() {
    return new Promise<Array<LanguagesProfile>>((resolve, reject) => {
      this.get<Array<LanguagesProfile>>("/languages/profiles")
        .then((result) => resolve(result.data))
        .catch(reject);
    });
  }

  async status() {
    return new Promise<SystemStatusResult>((resolve, reject) => {
      this.get<DataWrapper<SystemStatusResult>>("/status")
        .then((result) => {
          resolve(result.data.data);
        })
        .catch((reason) => {
          reject(reason);
        });
    });
  }

  async logs() {
    return new Promise<Array<SystemLog>>((resolve, reject) => {
      this.get<DataWrapper<Array<SystemLog>>>("/logs")
        .then((result) => resolve(result.data.data))
        .catch((err) => reject(err));
    });
  }

  async deleteLogs() {
    return new Promise<void>((resolve, reject) => {
      this.delete<void>("/logs")
        .then(() => resolve())
        .catch((err) => reject(err));
    });
  }

  async getTasks() {
    return new Promise<SystemTaskResult>((resolve, reject) => {
      this.get<DataWrapper<SystemTaskResult>>("/tasks")
        .then((result) => {
          resolve(result.data.data);
        })
        .catch((reason) => {
          reject(reason);
        });
    });
  }

  async execTasks(id: string) {
    return new Promise<void>((resolve, reject) => {
      this.postForm<void>("/tasks", { taskid: id })
        .then(() => {
          resolve();
        })
        .catch((reason) => {
          reject(reason);
        });
    });
  }
}

export default new SystemApi();
