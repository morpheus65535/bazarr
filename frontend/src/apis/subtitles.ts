import BaseApi from "./base";

type SubtitleType = "episode" | "movie";

class SubtitlesApi extends BaseApi {
  constructor() {
    super("/subtitles");
  }

  async info(names: string[]) {
    return new Promise<SubtitleInfo[]>((resolve, reject) => {
      this.get<DataWrapper<SubtitleInfo[]>>(`/info`, {
        filenames: names,
      })
        .then((result) => resolve(result.data.data))
        .catch(reject);
    });
  }

  async modify(
    action: string,
    id: number,
    type: SubtitleType,
    language: string,
    path: string
  ) {
    return new Promise<void>((resolve, reject) => {
      this.patch<void>(
        "",
        {
          type,
          id,
          language,
          path,
        },
        { action }
      )
        .then(() => resolve())
        .catch(reject);
    });
  }
}

export default new SubtitlesApi();
