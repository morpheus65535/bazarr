import BaseApi from "./base";

class FilesApi extends BaseApi {
  constructor() {
    super("/files");
  }

  async browse(name: string, path?: string) {
    const response = await this.get<FileTree[]>(name, { path });
    return response;
  }

  async bazarr(path?: string) {
    return this.browse("", path);
  }

  async sonarr(path?: string) {
    return this.browse("/sonarr", path);
  }

  async radarr(path?: string) {
    return this.browse("/radarr", path);
  }
}

export default new FilesApi();
