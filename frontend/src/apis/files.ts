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
}

export default new FilesApi();
