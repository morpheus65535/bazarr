import BaseApi from "./base";

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

  async modify(action: string, form: FormType.ModifySubtitle) {
    return new Promise<void>((resolve, reject) => {
      this.patch<void>("", form, { action })
        .then(() => resolve())
        .catch(reject);
    });
  }
}

export default new SubtitlesApi();
