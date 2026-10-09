import { camelCaseKeys, snakeCaseKeys } from "@/utilities/case";
import BaseApi from "./base";

class SubtitlesApi extends BaseApi {
  constructor() {
    super("/subtitles");
  }

  async getRefTracksByEpisodeId(
    subtitlesPath: string,
    sonarrEpisodeId: number,
  ) {
    const response = await this.get<DataWrapper<Item.RawRefTracks>>("", {
      subtitlesPath,
      sonarrEpisodeId,
    });
    return camelCaseKeys(response.data);
  }

  async getRefTracksByMovieId(
    subtitlesPath: string,
    radarrMovieId?: number | undefined,
  ) {
    const response = await this.get<DataWrapper<Item.RawRefTracks>>("", {
      subtitlesPath,
      radarrMovieId,
    });
    return camelCaseKeys(response.data);
  }

  async info(names: string[]) {
    const response = await this.get<DataWrapper<SubtitleInfo[]>>(`/info`, {
      filenames: names,
    });
    return response.data;
  }

  async modify(action: string, form: FormType.ModifySubtitle) {
    const payload = snakeCaseKeys(form);
    const cleaned = Object.fromEntries(
      Object.entries(payload)
        .filter(([, value]) => value != null)
        .filter(([key]) => key !== "media_title"),
    );
    await this.patch("", cleaned, { action });
  }

  async contents(subtitlePath: string) {
    const response = await this.get<DataWrapper<SubtitleContents.RawLine[]>>(
      "/contents",
      {
        subtitlePath,
      },
    );
    return response.data.map((line) => camelCaseKeys(line));
  }
}

const subtitlesApi = new SubtitlesApi();
export default subtitlesApi;
