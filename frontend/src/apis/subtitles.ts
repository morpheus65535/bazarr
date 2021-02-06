import BasicApi from "./basic";

class SubtitlesApi extends BasicApi {
  constructor() {
    super("/subtitles");
  }

  async info(names: string[]) {
    return new Promise<SubtitleNameInfo[]>((resolve, reject) => {
      this.get<DataWrapper<SubtitleNameInfo[]>>(`/info`, {
        filenames: names,
      })
        .then((result) => resolve(result.data.data))
        .catch(reject);
    });
  }

  async modify(action: string, language: string, path: string) {
    return new Promise<void>((resolve, reject) => {
      this.patch<void>(
        "",
        {
          language,
          path,
        },
        { action }
      )
        .then(() => resolve())
        .catch(reject);
    });
  }

  async sync(
    language: string,
    path: string,
    type: "episode" | "movie",
    id: number
  ) {
    return new Promise<void>((resolve, reject) => {
      this.patch<void>(
        "",
        {
          language,
          path,
          type,
          id,
        },
        { action: "sync" }
      )
        .then(() => resolve())
        .catch(reject);
    });
  }

  async translate(
    type: "series" | "movie",
    id: number,
    path: string,
    videoPath: string,
    language: string
  ) {
    return new Promise<void>((resolve, reject) => {
      this.patch<void>(
        "",
        {
          type,
          id,
          language,
          path,
          videoPath,
        },
        { action: "translate" }
      )
        .then(() => resolve())
        .catch(reject);
    });
  }
}

export default new SubtitlesApi();
