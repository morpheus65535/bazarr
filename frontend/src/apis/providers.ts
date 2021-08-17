import BaseApi from "./base";

class ProviderApi extends BaseApi {
  constructor() {
    super("/providers");
  }

  async providers(history: boolean = false) {
    const response = await this.get<DataWrapper<System.Provider[]>>("", {
      history,
    });
    return response.data;
  }

  async reset() {
    await this.post("", { action: "reset" });
  }

  async movies(id: number) {
    const response = await this.get<DataWrapper<SearchResultType[]>>(
      "/movies",
      { radarrid: id }
    );
    return response.data;
  }

  async downloadMovieSubtitle(radarrid: number, form: FormType.ManualDownload) {
    await this.post("/movies", form, { radarrid });
  }

  async episodes(episodeid: number) {
    const response = await this.get<DataWrapper<SearchResultType[]>>(
      "/episodes",
      {
        episodeid,
      }
    );
    return response.data;
  }

  async downloadEpisodeSubtitle(
    seriesid: number,
    episodeid: number,
    form: FormType.ManualDownload
  ) {
    await this.post("/episodes", form, { seriesid, episodeid });
  }
}

export default new ProviderApi();
