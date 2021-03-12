import BaseApi from "./base";

class SystemApi extends BaseApi {
  constructor() {
    super("/system");
  }

  private async performAction(action: string) {
    return new Promise((resolve, reject) => {
      this.post<void>("", undefined, { action })
        .then(resolve)
        .catch(reject);
    });
  }

  async login(username: string, password: string) {
    return new Promise((resolve, reject) => {
      this.post<void>("/account", { username, password }, { action: "login" })
        .then(resolve)
        .catch(reject);
    });
  }

  async logout() {
    return new Promise((resolve, reject) => {
      this.post<void>("/account", undefined, { action: "logout" })
        .then(resolve)
        .catch(reject);
    });
  }

  async shutdown() {
    return this.performAction("shutdown");
  }

  async restart() {
    return this.performAction("restart");
  }

  async settings() {
    return new Promise<Settings>((resolve, reject) => {
      this.get<Settings>("/settings")
        .then((result) => {
          resolve(result.data);
        })
        .catch(reject);
    });
  }

  async setSettings(data: object) {
    return new Promise<void>((resolve, reject) => {
      this.post<void>("/settings", data)
        .then((res) => {
          resolve();
        })
        .catch(reject);
    });
  }

  async languages() {
    return new Promise<Array<ApiLanguage>>((resolve, reject) => {
      this.get<Array<ApiLanguage>>("/languages")
        .then((result) => {
          resolve(result.data);
        })
        .catch((reason) => {
          reject(reason);
        });
    });
  }

  async languagesProfileList() {
    return new Promise<Array<Profile.Languages>>((resolve, reject) => {
      this.get<Array<Profile.Languages>>("/languages/profiles")
        .then((result) => resolve(result.data))
        .catch(reject);
    });
  }

  async status() {
    return new Promise<System.Status>((resolve, reject) => {
      this.get<DataWrapper<System.Status>>("/status")
        .then((result) => {
          resolve(result.data.data);
        })
        .catch((reason) => {
          reject(reason);
        });
    });
  }

  async logs() {
    return new Promise<Array<System.Log>>((resolve, reject) => {
      this.get<DataWrapper<Array<System.Log>>>("/logs")
        .then((result) => resolve(result.data.data))
        .catch((err) => reject(err));
    });
  }

  async releases() {
    return new Promise<Array<ReleaseInfo>>((resolve, reject) => {
      this.get<DataWrapper<Array<ReleaseInfo>>>("/releases")
        .then((result) => resolve(result.data.data))
        .catch(reject);
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
    return new Promise<System.Task>((resolve, reject) => {
      this.get<DataWrapper<System.Task>>("/tasks")
        .then((result) => {
          resolve(result.data.data);
        })
        .catch((reason) => {
          reject(reason);
        });
    });
  }

  async runTask(id: string) {
    return new Promise<void>((resolve, reject) => {
      this.post<void>("/tasks", { taskid: id })
        .then(() => {
          resolve();
        })
        .catch((reason) => {
          reject(reason);
        });
    });
  }

  async testNotification(protocol: string, path: string) {
    return new Promise<void>((resolve, reject) => {
      this.patch<void>("/notifications", { protocol, path })
        .then(() => resolve())
        .catch(reject);
    });
  }
}

export default new SystemApi();
