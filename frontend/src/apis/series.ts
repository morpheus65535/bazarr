import BaseApi from "./base";

class SeriesApi extends BaseApi {
  constructor() {
    super("/series");
  }

  async series(id?: number): Promise<Array<Item.Series>> {
    return new Promise<Array<Item.Series>>((resolve, reject) => {
      this.get<DataWrapper<Array<Item.Series>>>("", { seriesid: id })
        .then((result) => {
          resolve(result.data.data);
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
