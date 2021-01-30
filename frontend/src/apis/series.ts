import BasicApi from "./basic";

class SeriesApi extends BasicApi {
  constructor() {
    super("/series");
  }

  async blacklist(): Promise<Array<SeriesBlacklist>> {
    return new Promise<Array<SeriesBlacklist>>((resolve, reject) => {
      this.get<DataWrapper<Array<SeriesBlacklist>>>("/blacklist")
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

  async series(id?: number): Promise<Array<Series>> {
    return new Promise<Array<Series>>((resolve, reject) => {
      this.get<DataWrapper<Array<Series>>>("", { seriesid: id })
        .then((result) => {
          resolve(result.data.data);
        })
        .catch((reason) => {
          reject(reason);
        });
    });
  }

  async modify(form: SeriesModifyForm) {
    return new Promise<void>((resolve, reject) => {
      this.post<void>("", { ...form })
        .then(() => resolve())
        .catch((err) => reject(err));
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

  async scanDisk(id: number): Promise<void> {
    return new Promise<void>((resolve, reject) => {
      this.patch("/disk", undefined, { seriesid: id })
        .then(() => resolve())
        .catch(reject);
    });
  }

  async searchMissing(id: number): Promise<void> {
    return new Promise<void>((resolve, reject) => {
      this.patch("/missing", undefined, { seriesid: id })
        .then(() => resolve())
        .catch(reject);
    });
  }
}

export default new SeriesApi();
