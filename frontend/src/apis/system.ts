import BasicApi from "./basic";

class SystemApi extends BasicApi {
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
      this.post<void>("/settings", data)
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
}

export default new SystemApi();
