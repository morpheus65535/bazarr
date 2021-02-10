import BasicApi from "./basic";

class FilesApi extends BasicApi {
  constructor() {
    super("/files");
  }

  async browse(name: string, path?: string): Promise<FileTree[]> {
    return new Promise((resolve, reject) => {
      this.get<FileTree[]>(name, { path })
        .then((res) => resolve(res.data))
        .catch(reject);
    });
  }

  async bazarr(path?: string): Promise<FileTree[]> {
    return this.browse("", path);
  }

  async sonarr(path?: string): Promise<FileTree[]> {
    return this.browse("sonarr", path);
  }

  async radarr(path?: string): Promise<FileTree[]> {
    return this.browse("radarr", path);
  }
}

export default new FilesApi();
