import BaseApi from "./base";

class EpisodeApi extends BaseApi {
  constructor() {
    super("/episodes");
  }

  async bySeriesId(seriesid: number[]) {
    const response = await this.get<DataWrapper<Item.Episode[]>>("", {
      seriesid,
    });
    return response.data;
  }

  async byEpisodeId(episodeid: number[]) {
    const response = await this.get<DataWrapper<Item.Episode[]>>("", {
      episodeid,
    });
    return response.data;
  }

  async wanted(params: Parameter.Range) {
    const response = await this.get<DataWrapperWithTotal<Wanted.Episode>>(
      "/wanted",
      params
    );
    return response;
  }

  async wantedBy(episodeid: number[]) {
    const response = await this.get<DataWrapperWithTotal<Wanted.Episode>>(
      "/wanted",
      { episodeid }
    );
    return response;
  }

  async history(params: Parameter.Range) {
    const response = await this.get<DataWrapperWithTotal<History.Episode>>(
      "/history",
      params
    );
    return response;
  }

  async historyBy(episodeid: number) {
    const response = await this.get<DataWrapperWithTotal<History.Episode>>(
      "/history",
      { episodeid }
    );
    return response;
  }

  async downloadSubtitles(
    seriesid: number,
    episodeid: number,
    form: FormType.Subtitle
  ) {
    await this.patch("/subtitles", form, { seriesid, episodeid });
  }

  async uploadSubtitles(
    seriesid: number,
    episodeid: number,
    form: FormType.UploadSubtitle
  ) {
    await this.post("/subtitles", form, { seriesid, episodeid });
  }

  async deleteSubtitles(
    seriesid: number,
    episodeid: number,
    form: FormType.DeleteSubtitle
  ) {
    await this.delete("/subtitles", form, { seriesid, episodeid });
  }

  async blacklist() {
    const response = await this.get<DataWrapper<Blacklist.Episode[]>>(
      "/blacklist"
    );
    return response.data;
  }

  async addBlacklist(
    seriesid: number,
    episodeid: number,
    form: FormType.AddBlacklist
  ) {
    await this.post("/blacklist", form, { seriesid, episodeid });
  }

  async deleteBlacklist(all?: boolean, form?: FormType.DeleteBlacklist) {
    await this.delete("/blacklist", form, { all });
  }
}

export default new EpisodeApi();
