import BaseApi from "./base";

class HistoryApi extends BaseApi {
  constructor() {
    super("/history");
  }

  async stats(
    timeFrame?: History.TimeFrameOptions,
    action?: History.ActionOptions,
    provider?: string,
    language?: Language.CodeType
  ) {
    const response = await this.get<History.Stat>("/stats", {
      timeFrame,
      action,
      provider,
      language,
    });
    return response;
  }
}

export default new HistoryApi();
