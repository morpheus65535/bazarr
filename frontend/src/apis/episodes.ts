import BaseApi from "./base";

class EpisodeApi extends BaseApi {
  constructor() {
    super("/episodes");
  }

  async bySeriesId(seriesid: number): Promise<Array<Item.Episode>> {
    return new Promise<Array<Item.Episode>>((resolve, reject) => {
      this.get<DataWrapper<Array<Item.Episode>>>("", { seriesid })
        .then((result) => {
          resolve(result.data.data);
        })
        .catch((reason) => {
          reject(reason);
        });
    });
  }

  async wanted(): Promise<Array<Wanted.Episode>> {
    return new Promise<Array<Wanted.Episode>>((resolve, reject) => {
      this.get<DataWrapper<Array<Wanted.Episode>>>("/wanted")
        .then((result) => {
          resolve(result.data.data);
        })
        .catch((reason) => {
          reject(reason);
        });
    });
  }

  async byEpisodeId(episodeid: number): Promise<Array<Item.Episode>> {
    return new Promise<Array<Item.Episode>>((resolve, reject) => {
      this.get<DataWrapper<Array<Item.Episode>>>("", { episodeid })
        .then((result) => {
          resolve(result.data.data);
        })
        .catch((reason) => {
          reject(reason);
        });
    });
  }

  async history(episodeid?: number): Promise<Array<History.Episode>> {
    return new Promise<Array<History.Episode>>((resolve, reject) => {
      this.get<DataWrapper<Array<History.Episode>>>("/history", { episodeid })
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
    form: FormType.Subtitle
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
    form: FormType.UploadSubtitle
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
    form: FormType.DeleteSubtitle
  ): Promise<void> {
    return new Promise<void>((resolve, reject) => {
      this.delete("/subtitles", form, { seriesid, episodeid })
        .then(() => resolve())
        .catch(reject);
    });
  }

  async blacklist(): Promise<Array<Blacklist.Episode>> {
    return new Promise<Array<Blacklist.Episode>>((resolve, reject) => {
      this.get<DataWrapper<Array<Blacklist.Episode>>>("/blacklist")
        .then((res) => {
          resolve(res.data.data);
        })
        .catch(reject);
    });
  }

  async addBlacklist(
    seriesid: number,
    episodeid: number,
    form: FormType.AddBlacklist
  ): Promise<void> {
    return new Promise((resolve, reject) => {
      this.post<void>("/blacklist", form, { seriesid, episodeid })
        .then(() => resolve())
        .catch(reject);
    });
  }

  async deleteBlacklist(
    all?: boolean,
    form?: FormType.DeleteBlacklist
  ): Promise<void> {
    return new Promise((resolve, reject) => {
      this.delete<void>("/blacklist", form, { all })
        .then(() => resolve())
        .catch(reject);
    });
  }
}

export default new EpisodeApi();
