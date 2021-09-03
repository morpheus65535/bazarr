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

  async addBlacklist(movieid: number, form: FormType.AddBlacklist) {
    await this.post("/blacklist", form, { movieid });
  }

  async deleteBlacklist(all?: boolean, form?: FormType.DeleteBlacklist) {
    await this.delete("/blacklist", form, { all });
  }

  async movies(movieid?: number[]) {
    const response = await this.get<AsyncDataWrapper<Item.Movie>>("", {
      movieid,
    });
    return response;
  }

  async moviesBy(params: Parameter.Range) {
    const response = await this.get<AsyncDataWrapper<Item.Movie>>("", params);
    return response;
  }

  async modify(form: FormType.ModifyItem) {
    await this.post("", { movieid: form.id, profileid: form.profileid });
  }

  async wanted(params: Parameter.Range) {
    const response = await this.get<AsyncDataWrapper<Wanted.Movie>>(
      "/wanted",
      params
    );
    return response;
  }

  async wantedBy(movieid: number[]) {
    const response = await this.get<AsyncDataWrapper<Wanted.Movie>>("/wanted", {
      movieid,
    });
    return response;
  }

  async history(params: Parameter.Range) {
    const response = await this.get<AsyncDataWrapper<History.Movie>>(
      "/history",
      params
    );
    return response;
  }

  async historyBy(movieid: number) {
    const response = await this.get<AsyncDataWrapper<History.Movie>>(
      "/history",
      { movieid }
    );
    return response;
  }

  async action(action: FormType.MoviesAction) {
    await this.patch("", action);
  }

  async downloadSubtitles(movieid: number, form: FormType.Subtitle) {
    await this.patch("/subtitles", form, { movieid });
  }

  async uploadSubtitles(movieid: number, form: FormType.UploadSubtitle) {
    await this.post("/subtitles", form, { movieid });
  }

  async deleteSubtitles(movieid: number, form: FormType.DeleteSubtitle) {
    await this.delete("/subtitles", form, { movieid });
  }
}

export default new MovieApi();
