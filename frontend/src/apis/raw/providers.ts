import { camelCaseKeys, snakeCaseKeys } from "@/utilities/case";
import BaseApi from "./base";

class ProviderApi extends BaseApi {
  constructor() {
    super("/providers");
  }

  async providers(history = false) {
    const response = await this.get<DataWrapper<System.Provider[]>>("", {
      history,
    });
    return response.data;
  }

  async reset() {
    await this.post("", { action: "reset" });
  }

  async movies(id: number) {
    const response = await this.get<DataWrapper<RawSearchResultType[]>>(
      "/movies",
      { radarrid: id },
    );
    return response.data.map(camelCaseKeys);
  }

  async downloadMovieSubtitle(radarrid: number, form: FormType.ManualDownload) {
    await this.post("/movies", snakeCaseKeys(form), { radarrid });
  }

  async episodes(episodeid: number) {
    const response = await this.get<DataWrapper<RawSearchResultType[]>>(
      "/episodes",
      {
        episodeid,
      },
    );
    return response.data.map(camelCaseKeys);
  }

  async downloadEpisodeSubtitle(
    seriesid: number,
    episodeid: number,
    form: FormType.ManualDownload,
  ) {
    await this.post("/episodes", snakeCaseKeys(form), { seriesid, episodeid });
  }
}

const providerApi = new ProviderApi();
export default providerApi;
