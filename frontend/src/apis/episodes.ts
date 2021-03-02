import BaseApi from "./base";

class EpisodeApi extends BaseApi {
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

  async wanted(): Promise<Array<WantedEpisode>> {
    return new Promise<Array<WantedEpisode>>((resolve, reject) => {
      this.get<DataWrapper<Array<WantedEpisode>>>("/wanted")
        .then((result) => {
          resolve(result.data.data);
        })
        .catch((reason) => {
          reject(reason);
        });
    });
  }

  async searchAllWanted(): Promise<void> {
    return new Promise<void>((resolve, reject) => {
      this.patch("/wanted")
        .then(() => resolve())
        .catch(reject);
    });
  }

  async episode(episodeid: number): Promise<Array<Episode>> {
    return new Promise<Array<Episode>>((resolve, reject) => {
      this.get<DataWrapper<Array<Episode>>>("", { episodeid })
        .then((result) => {
          resolve(result.data.data);
        })
        .catch((reason) => {
          reject(reason);
        });
    });
  }

  async history(episodeid?: number): Promise<Array<EpisodeHistory>> {
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

  async blacklist(): Promise<Array<EpisodeBlacklist>> {
    return new Promise<Array<EpisodeBlacklist>>((resolve, reject) => {
      this.get<DataWrapper<Array<EpisodeBlacklist>>>("/blacklist")
        .then((res) => {
          resolve(res.data.data);
        })
        .catch(reject);
    });
  }

  async addBlacklist(
    seriesid: number,
    episodeid: number,
    form: BlacklistAddForm
  ): Promise<void> {
    return new Promise((resolve, reject) => {
      this.post<void>("/blacklist", form, { seriesid, episodeid })
        .then(() => resolve())
        .catch(reject);
    });
  }

  async deleteBlacklist(
    all?: boolean,
    form?: BlacklistDeleteForm
  ): Promise<void> {
    return new Promise((resolve, reject) => {
      this.delete<void>("/blacklist", form, { all })
        .then(() => resolve())
        .catch(reject);
    });
  }
}

export default new EpisodeApi();
