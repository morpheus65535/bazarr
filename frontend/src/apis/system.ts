import { AxiosResponse } from "axios";
import { ThemeConsumer } from "react-bootstrap/esm/ThemeProvider";
import apis from ".";

class SystemApi {
  get<T>(path: string, params?: any): Promise<AxiosResponse<T>> {
    return apis.axios.get(`/system/${path}`, { params });
  }

  postForm<T>(
    path: string,
    formdata?: any,
    params?: any
  ): Promise<AxiosResponse<T>> {
    return apis.post(`/system/${path}`, formdata, params);
  }

  delete<T>(path: string, params?: any): Promise<AxiosResponse<T>> {
    return apis.axios.delete(`/system/${path}`, { params });
  }

  async shutdown() {
    return this.get<void>("shutdown");
  }

  async restart() {
    return this.get<void>("restart");
  }

  async languages(enabled: boolean = false) {
    return new Promise<Array<ExtendLanguage>>((resolve, reject) => {
      this.get<Array<ExtendLanguage>>("languages", { enabled })
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
      this.get<DataWrapper<SystemStatusResult>>("status")
        .then((result) => {
          resolve(result.data.data);
        })
        .catch((reason) => {
          reject(reason);
        });
    });
  }

  async providers() {
    return new Promise<Array<SystemProvider>>((resolve, reject) => {
      this.get<DataWrapper<Array<SystemProvider>>>("providers")
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
      this.get<DataWrapper<Array<SystemLog>>>("logs")
        .then((result) => resolve(result.data.data))
        .catch((err) => reject(err));
    });
  }

  async deleteLogs() {
    return new Promise<void>((resolve, reject) => {
      this.delete<void>("logs")
        .then(() => resolve())
        .catch((err) => reject(err));
    });
  }

  async getTasks() {
    return new Promise<SystemTaskResult>((resolve, reject) => {
      this.get<DataWrapper<SystemTaskResult>>("tasks")
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
      this.postForm<void>("tasks", { taskid: id })
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
