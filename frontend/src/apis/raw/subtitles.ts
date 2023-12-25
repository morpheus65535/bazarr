import BaseApi from "./base";

class SubtitlesApi extends BaseApi {
  constructor() {
    super("/subtitles");
  }

  async getRefTracksById(
    subtitlesPath: string,
    sonarrEpisodeId?: number | undefined,
    radarrMovieId?: number | undefined
  ) {
    if (sonarrEpisodeId) {
      const response = await this.get<DataWrapper<Item.RefTracks>>("", {
        subtitlesPath,
        sonarrEpisodeId,
      });
      return response.data;
    } else {
      const response = await this.get<DataWrapper<Item.RefTracks>>("", {
        subtitlesPath,
        radarrMovieId,
      });
      return response.data;
    }
  }

  async info(names: string[]) {
    const response = await this.get<DataWrapper<SubtitleInfo[]>>(`/info`, {
      filenames: names,
    });
    return response.data;
  }

  async modify(action: string, form: FormType.ModifySubtitle) {
    await this.patch("", form, { action });
  }
}

const subtitlesApi = new SubtitlesApi();
export default subtitlesApi;
