import BaseApi from "./base";

class SeriesApi extends BaseApi {
  constructor() {
    super("/series");
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

  async modify(form: ItemModifyForm) {
    return new Promise<void>((resolve, reject) => {
      this.post<void>("", { seriesid: form.id, profileid: form.profileid })
        .then(() => resolve())
        .catch((err) => reject(err));
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
