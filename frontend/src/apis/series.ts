import BaseApi from "./base";

class SeriesApi extends BaseApi {
  constructor() {
    super("/series");
  }

  async series(seriesid?: number[]) {
    return new Promise<AsyncDataWrapper<Item.Series>>((resolve, reject) => {
      this.get<AsyncDataWrapper<Item.Series>>("", { seriesid })
        .then((result) => {
          resolve(result.data);
        })
        .catch((reason) => {
          reject(reason);
        });
    });
  }

  async seriesBy(start: number, length: number) {
    return new Promise<AsyncDataWrapper<Item.Series>>((resolve, reject) => {
      this.get<AsyncDataWrapper<Item.Series>>("", { start, length })
        .then((result) => {
          resolve(result.data);
        })
        .catch((reason) => {
          reject(reason);
        });
    });
  }

  async modify(form: FormType.ModifyItem) {
    return new Promise<void>((resolve, reject) => {
      this.post<void>("", { seriesid: form.id, profileid: form.profileid })
        .then(() => resolve())
        .catch((err) => reject(err));
    });
  }

  async action(form: FormType.SeriesAction) {
    return new Promise<void>((resolve, reject) => {
      this.patch("", form)
        .then(() => resolve())
        .catch(reject);
    });
  }
}

export default new SeriesApi();
