import BaseApi from "./base";

class NewPlexApi extends BaseApi {
  constructor() {
    super("/plex");
  }

  async createPin() {
    const response = await this.post<DataWrapper<Plex.Pin>>("/oauth/pin", {});

    return response.data;
  }

  async checkPin(pinId: string) {
    // TODO: Can this be replaced with params instead of passing a variable in the path?
    const response = await this.get<DataWrapper<Plex.PinCheckResult>>(
      `/oauth/pin/${pinId}/check`,
    );

    return response.data;
  }

  async logout() {
    await this.post(`/oauth/logout`, {});
  }

  async servers() {
    const response =
      await this.get<DataWrapper<Plex.Server[]>>(`/oauth/servers`);

    return response.data;
  }

  async selectServer(form: FormType.PlexSelectServer) {
    // Flatten the nested connection object for form data
    const flattenedForm = {
      machineIdentifier: form.machineIdentifier,
      name: form.name,
      "connection.uri": form.connection.uri,
      "connection.local": form.connection.local.toString(),
    };

    const response = await this.post<DataWrapper<Plex.Server>>(
      "/select-server",
      flattenedForm,
    );

    return response.data;
  }

  async selectedServer() {
    const response = await this.get<DataWrapper<Plex.Server>>(`/select-server`);

    return response.data;
  }

  async validateAuth() {
    const response =
      await this.get<DataWrapper<Plex.ValidationResult>>(`/oauth/validate`);

    return response.data;
  }
}

export default new NewPlexApi();
