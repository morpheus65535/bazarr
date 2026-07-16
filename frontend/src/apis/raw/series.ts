import { camelCaseKeys, snakeCaseKeys } from "@/utilities/case";
import BaseApi from "./base";

class SeriesApi extends BaseApi {
  constructor() {
    super("/series");
  }

  async series(seriesid?: number[]) {
    const response = await this.get<DataWrapperWithTotal<Item.RawSeries>>("", {
      seriesid,
    });
    return response.data.map(camelCaseKeys);
  }

  async seriesBy(params: Parameter.Range) {
    const response = await this.get<DataWrapperWithTotal<Item.RawSeries>>(
      "",
      params,
    );
    return {
      ...response,
      data: response.data.map(camelCaseKeys),
    };
  }

  async modify(form: FormType.ModifyItem) {
    await this.post("", { seriesid: form.id, profileid: form.profileId });
  }

  async action(form: FormType.SeriesAction) {
    await this.patch("", snakeCaseKeys(form));
  }
}

const seriesApi = new SeriesApi();
export default seriesApi;
