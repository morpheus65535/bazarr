import BaseApi from "./base";

class SystemApi extends BaseApi {
  constructor() {
    super("/system");
  }

  private async performAction(action: string) {
    await this.post("", undefined, { action });
  }

  async login(username: string, password: string) {
    await this.post("/account", { username, password }, { action: "login" });
  }

  async logout() {
    await this.post("/account", undefined, { action: "logout" });
  }

  async shutdown() {
    return this.performAction("shutdown");
  }

  async restart() {
    return this.performAction("restart");
  }

  async settings() {
    const response = await this.get<Settings>("/settings");
    return response;
  }

  async setSettings(data: object) {
    await this.post("/settings", data);
  }

  async languages(history: boolean = false) {
    const response = await this.get<Language.Server[]>("/languages", {
      history,
    });
    return response;
  }

  async languagesProfileList() {
    const response = await this.get<Language.Profile[]>("/languages/profiles");
    return response;
  }

  async status() {
    const response = await this.get<DataWrapper<System.Status>>("/status");
    return response.data;
  }

  async health() {
    const response = await this.get<DataWrapper<System.Health[]>>("/health");
    return response.data;
  }

  async logs() {
    const response = await this.get<DataWrapper<System.Log[]>>("/logs");
    return response.data;
  }

  async releases() {
    const response = await this.get<DataWrapper<ReleaseInfo[]>>("/releases");
    return response.data;
  }

  async deleteLogs() {
    await this.delete("/logs");
  }

  async tasks() {
    const response = await this.get<DataWrapper<System.Task[]>>("/tasks");
    return response.data;
  }

  async runTask(taskid: string) {
    await this.post("/tasks", { taskid });
  }

  async testNotification(url: string) {
    await this.patch("/notifications", { url });
  }

  async search(query: string) {
    const response = await this.get<ItemSearchResult[]>("/searches", { query });
    return response;
  }
}

export default new SystemApi();
