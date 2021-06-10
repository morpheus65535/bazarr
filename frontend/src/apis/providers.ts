import BaseApi from "./base";

class ProviderApi extends BaseApi {
  constructor() {
    super("/providers");
  }

  async providers(history: boolean = false) {
    return new Promise<Array<System.Provider>>((resolve, reject) => {
      this.get<DataWrapper<Array<System.Provider>>>("", { history })
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
    return new Promise<SearchResultType[]>((resolve, reject) => {
      this.get<DataWrapper<SearchResultType[]>>("/movies", { radarrid: id })
        .then((result) => resolve(result.data.data))
        .catch(reject);
    });
  }

  async downloadMovieSubtitle(radarrid: number, form: FormType.ManualDownload) {
    return new Promise<void>((resolve, reject) => {
      this.post<void>("/movies", form, { radarrid })
        .then(() => resolve())
        .catch(reject);
    });
  }

  async episodes(id: number) {
    return new Promise<SearchResultType[]>((resolve, reject) => {
      this.get<DataWrapper<SearchResultType[]>>("/episodes", {
        episodeid: id,
      })
        .then((result) => resolve(result.data.data))
        .catch(reject);
    });
  }

  async downloadEpisodeSubtitle(
    seriesid: number,
    episodeid: number,
    form: FormType.ManualDownload
  ) {
    return new Promise<void>((resolve, reject) => {
      this.post<void>("/episodes", form, { seriesid, episodeid })
        .then(() => resolve())
        .catch(reject);
    });
  }
}

export default new ProviderApi();
