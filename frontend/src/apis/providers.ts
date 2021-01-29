import BasicApi from "./basic";

class ProviderApi extends BasicApi {
  constructor() {
    super("/providers");
  }

  async providers() {
    return new Promise<Array<SystemProvider>>((resolve, reject) => {
      this.get<DataWrapper<Array<SystemProvider>>>("")
        .then((result) => {
          resolve(result.data.data);
        })
        .catch(reject);
    });
  }

  async reset() {
    return new Promise<void>((resolve, reject) => {
      this.post<void>("", { action: "reset" })
        .then(() => resolve())
        .catch(reject);
    });
  }

  async movies(id: number) {
    return new Promise<ManualSearchResult[]>((resolve, reject) => {
      this.get<DataWrapper<ManualSearchResult[]>>("/movies", { radarrid: id })
        .then((result) => resolve(result.data.data))
        .catch(reject);
    });
  }

  async downloadMovieSubtitle(radarrid: number, form: ManualDownloadForm) {
    return new Promise<void>((resolve, reject) => {
      this.post<void>("/movies", form, { radarrid })
        .then(() => resolve())
        .catch(reject);
    });
  }

  async episodes(id: number) {
    return new Promise<ManualSearchResult[]>((resolve, reject) => {
      this.get<DataWrapper<ManualSearchResult[]>>("/episodes", {
        episodeid: id,
      })
        .then((result) => resolve(result.data.data))
        .catch(reject);
    });
  }

  async downloadEpisodeSubtitle(
    seriesid: number,
    episodeid: number,
    form: ManualDownloadForm
  ) {
    return new Promise<void>((resolve, reject) => {
      this.post<void>("/episodes", form, { seriesid, episodeid })
        .then(() => resolve())
        .catch(reject);
    });
  }
}

export default new ProviderApi();
