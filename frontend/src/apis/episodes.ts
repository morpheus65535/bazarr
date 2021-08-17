import BaseApi from "./base";

class EpisodeApi extends BaseApi {
  constructor() {
    super("/episodes");
  }

  async bySeriesId(seriesid: number[]): Promise<Item.Episode[]> {
    return new Promise<Item.Episode[]>((resolve, reject) => {
      this.get<DataWrapper<Item.Episode[]>>("", { seriesid })
        .then((result) => {
          resolve(result.data.data);
        })
        .catch((reason) => {
          reject(reason);
        });
    });
  }

  async byEpisodeId(episodeid: number[]): Promise<Item.Episode[]> {
    return new Promise<Item.Episode[]>((resolve, reject) => {
      this.get<DataWrapper<Item.Episode[]>>("", { episodeid })
        .then((result) => {
          resolve(result.data.data);
        })
        .catch((reason) => {
          reject(reason);
        });
    });
  }

  async wanted(params: Parameter.Range) {
    return new Promise<AsyncDataWrapper<Wanted.Episode>>((resolve, reject) => {
      this.get<AsyncDataWrapper<Wanted.Episode>>("/wanted", params)
        .then((result) => {
          resolve(result.data);
        })
        .catch((reason) => {
          reject(reason);
        });
    });
  }

  async wantedBy(episodeid: number[]) {
    return new Promise<AsyncDataWrapper<Wanted.Episode>>((resolve, reject) => {
      this.get<AsyncDataWrapper<Wanted.Episode>>("/wanted", { episodeid })
        .then((result) => {
          resolve(result.data);
        })
        .catch((reason) => {
          reject(reason);
        });
    });
  }

  async history(params: Parameter.Range) {
    const response = await this.get<AsyncDataWrapper<History.Episode>>(
      "/history",
      params
    );
    return response.data;
  }

  async historyBy(episodeid: number) {
    const response = await this.get<AsyncDataWrapper<History.Episode>>(
      "/history",
      { episodeid }
    );
    return response.data;
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

  async blacklist(): Promise<Blacklist.Episode[]> {
    return new Promise<Blacklist.Episode[]>((resolve, reject) => {
      this.get<DataWrapper<Blacklist.Episode[]>>("/blacklist")
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
