import BaseApi from "./base";

class MovieApi extends BaseApi {
  constructor() {
    super("/movies");
  }

  async blacklist() {
    const response = await this.get<DataWrapper<Blacklist.Movie[]>>(
      "/blacklist"
    );
    return response.data;
  }

  async addBlacklist(radarrid: number, form: FormType.AddBlacklist) {
    await this.post("/blacklist", form, { radarrid });
  }

  async deleteBlacklist(all?: boolean, form?: FormType.DeleteBlacklist) {
    await this.delete("/blacklist", form, { all });
  }

  async movies(radarrid?: number[]) {
    const response = await this.get<DataWrapperWithTotal<Item.Movie>>("", {
      radarrid,
    });
    return response;
  }

  async moviesBy(params: Parameter.Range) {
    const response = await this.get<DataWrapperWithTotal<Item.Movie>>(
      "",
      params
    );
    return response;
  }

  async modify(form: FormType.ModifyItem) {
    await this.post("", { radarrid: form.id, profileid: form.profileid });
  }

  async wanted(params: Parameter.Range) {
    const response = await this.get<DataWrapperWithTotal<Wanted.Movie>>(
      "/wanted",
      params
    );
    return response;
  }

  async wantedBy(radarrid: number[]) {
    const response = await this.get<DataWrapperWithTotal<Wanted.Movie>>(
      "/wanted",
      {
        radarrid,
      }
    );
    return response;
  }

  async history(params: Parameter.Range) {
    const response = await this.get<DataWrapperWithTotal<History.Movie>>(
      "/history",
      params
    );
    return response;
  }

  async historyBy(radarrid: number) {
    const response = await this.get<DataWrapperWithTotal<History.Movie>>(
      "/history",
      { radarrid }
    );
    return response;
  }

  async action(action: FormType.MoviesAction) {
    await this.patch("", action);
  }

  async downloadSubtitles(radarrid: number, form: FormType.Subtitle) {
    await this.patch("/subtitles", form, { radarrid });
  }

  async uploadSubtitles(radarrid: number, form: FormType.UploadSubtitle) {
    await this.post("/subtitles", form, { radarrid });
  }

  async deleteSubtitles(radarrid: number, form: FormType.DeleteSubtitle) {
    await this.delete("/subtitles", form, { radarrid });
  }
}

export default new MovieApi();
