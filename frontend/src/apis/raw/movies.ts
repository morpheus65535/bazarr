import { camelCaseKeys, snakeCaseKeys } from "@/utilities/case";
import BaseApi from "./base";
import { buildListParams } from "./utils";

class MovieApi extends BaseApi {
  constructor() {
    super("/movies");
  }

  async blacklist() {
    const response =
      await this.get<DataWrapper<Blacklist.RawMovie[]>>("/blacklist");
    return response.data.map(camelCaseKeys);
  }

  async addBlacklist(radarrid: number, form: FormType.AddBlacklist) {
    await this.post("/blacklist", snakeCaseKeys(form), { radarrid });
  }

  async deleteBlacklist(all?: boolean, form?: FormType.DeleteBlacklist) {
    await this.delete("/blacklist", snakeCaseKeys(form), { all });
  }

  async movies(radarrid?: number[]) {
    const response = await this.get<DataWrapperWithTotal<Item.RawMovie>>("", {
      radarrid,
    });
    return response.data.map(camelCaseKeys);
  }

  async moviesBy(params: Parameter.ListQuery) {
    const response = await this.get<DataWrapperWithTotal<Item.RawMovie>>(
      "",
      buildListParams(params),
    );
    return {
      ...response,
      data: response.data.map(camelCaseKeys),
    };
  }

  async modify(form: FormType.ModifyItem) {
    await this.post("", { radarrid: form.id, profileid: form.profileId });
  }

  async tags() {
    const response = await this.get<DataWrapper<{ tag: string }[]>>("/tags");
    return response.data.map(({ tag }) => tag);
  }

  async wanted(params: Parameter.Range) {
    const response = await this.get<DataWrapperWithTotal<Wanted.RawMovie>>(
      "/wanted",
      params,
    );
    return {
      ...response,
      data: response.data.map(camelCaseKeys),
    };
  }

  async wantedBy(radarrid: number[]) {
    const response = await this.get<DataWrapperWithTotal<Wanted.RawMovie>>(
      "/wanted",
      {
        radarrid,
      },
    );
    return {
      ...response,
      data: response.data.map(camelCaseKeys),
    };
  }

  async history(params: Parameter.Range) {
    const response = await this.get<DataWrapperWithTotal<History.RawMovie>>(
      "/history",
      params,
    );
    return camelCaseKeys(response);
  }

  async historyBy(radarrid: number) {
    const response = await this.get<DataWrapperWithTotal<History.RawMovie>>(
      "/history",
      { radarrid },
    );
    return response.data.map(camelCaseKeys);
  }

  async action(form: FormType.MoviesAction) {
    const payload: Record<string, unknown> = { action: form.action };

    if (form.action !== "search-wanted") {
      payload.radarrid = form.radarrId;
    }

    await this.patch("", payload);
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

const movieApi = new MovieApi();
export default movieApi;
