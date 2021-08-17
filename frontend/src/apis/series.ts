import BaseApi from "./base";

class SeriesApi extends BaseApi {
  constructor() {
    super("/series");
  }

  async series(seriesid?: number[]) {
    const response = await this.get<AsyncDataWrapper<Item.Series>>("", {
      seriesid,
    });
    return response;
  }

  async seriesBy(params: Parameter.Range) {
    const response = await this.get<AsyncDataWrapper<Item.Series>>("", params);
    return response;
  }

  async modify(form: FormType.ModifyItem) {
    await this.post("", { seriesid: form.id, profileid: form.profileid });
  }

  async action(form: FormType.SeriesAction) {
    await this.patch("", form);
  }
}

export default new SeriesApi();
