import BasicApi from "./basic";

class EpisodeApi extends BasicApi {
  constructor() {
    super("/episodes");
  }

  async all(seriesid: number): Promise<Array<Episode>> {
    return new Promise<Array<Episode>>((resolve, reject) => {
      this.get<DataWrapper<Array<Episode>>>("", { seriesid })
        .then((result) => {
          resolve(result.data.data);
        })
        .catch((reason) => {
          reject(reason);
        });
    });
  }

  async history(episodeid: number): Promise<Array<EpisodeHistory>> {
    return new Promise<Array<EpisodeHistory>>((resolve, reject) => {
      this.get<DataWrapper<Array<EpisodeHistory>>>("/history", { episodeid })
        .then((result) => {
          resolve(result.data.data);
        })
        .catch((reason) => {
          reject(reason);
        });
    });
  }

  async downloadSubtitles(
    seriesid: number,
    episodeid: number,
    form: SubtitleForm
  ): Promise<void> {
    return new Promise<void>((resolve, reject) => {
      this.patch("/subtitles", form, { seriesid, episodeid })
        .then(() => resolve())
        .catch(reject);
    });
  }

  async uploadSubtitles(
    seriesid: number,
    episodeid: number,
    form: SubtitleUploadForm
  ): Promise<void> {
    return new Promise<void>((resolve, reject) => {
      this.post("/subtitles", form, { seriesid, episodeid })
        .then(() => resolve())
        .catch(reject);
    });
  }

  async deleteSubtitles(
    seriesid: number,
    episodeid: number,
    form: SubtitleDeleteForm
  ): Promise<void> {
    return new Promise<void>((resolve, reject) => {
      this.delete("/subtitles", form, { seriesid, episodeid })
        .then(() => resolve())
        .catch(reject);
    });
  }
}

export default new EpisodeApi();
