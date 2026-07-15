import { camelCaseKeys, snakeCaseKeys } from "@/utilities/case";
import BaseApi from "./base";

class EpisodeApi extends BaseApi {
  constructor() {
    super("/episodes");
  }

  async bySeriesId(seriesid: number[]) {
    const response = await this.get<DataWrapper<Item.RawEpisode[]>>("", {
      seriesid,
    });
    return response.data.map(camelCaseKeys);
  }

  async byEpisodeId(episodeid: number[]) {
    const response = await this.get<DataWrapper<Item.RawEpisode[]>>("", {
      episodeid,
    });
    return response.data.map(camelCaseKeys);
  }

  async wanted(params: Parameter.Range) {
    const response = await this.get<DataWrapperWithTotal<Wanted.RawEpisode>>(
      "/wanted",
      params,
    );
    return {
      ...response,
      data: response.data.map(camelCaseKeys),
    };
  }

  async wantedBy(episodeid: number[]) {
    const response = await this.get<DataWrapperWithTotal<Wanted.RawEpisode>>(
      "/wanted",
      { episodeid },
    );
    return {
      ...response,
      data: response.data.map(camelCaseKeys),
    };
  }

  async history(params: Parameter.Range) {
    const response = await this.get<DataWrapperWithTotal<History.RawEpisode>>(
      "/history",
      params,
    );
    return camelCaseKeys(response);
  }

  async historyBy(episodeid: number) {
    const response = await this.get<DataWrapperWithTotal<History.RawEpisode>>(
      "/history",
      { episodeid },
    );
    return response.data.map(camelCaseKeys);
  }

  async downloadSubtitles(
    seriesid: number,
    episodeid: number,
    form: FormType.Subtitle,
  ) {
    await this.patch("/subtitles", form, { seriesid, episodeid });
  }

  async uploadSubtitles(
    seriesid: number,
    episodeid: number,
    form: FormType.UploadSubtitle,
  ) {
    await this.post("/subtitles", form, { seriesid, episodeid });
  }

  async deleteSubtitles(
    seriesid: number,
    episodeid: number,
    form: FormType.DeleteSubtitle,
  ) {
    await this.delete("/subtitles", form, { seriesid, episodeid });
  }

  async blacklist() {
    const response =
      await this.get<DataWrapper<Blacklist.RawEpisode[]>>("/blacklist");
    return response.data.map(camelCaseKeys);
  }

  async addBlacklist(
    seriesid: number,
    episodeid: number,
    form: FormType.AddBlacklist,
  ) {
    await this.post("/blacklist", snakeCaseKeys(form), { seriesid, episodeid });
  }

  async deleteBlacklist(all?: boolean, form?: FormType.DeleteBlacklist) {
    await this.delete("/blacklist", snakeCaseKeys(form), { all });
  }
}

const episodeApi = new EpisodeApi();
export default episodeApi;
