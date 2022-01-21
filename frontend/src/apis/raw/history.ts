import BaseApi from "./base";

class HistoryApi extends BaseApi {
  constructor() {
    super("/history");
  }

  async stats(
    timeframe?: History.TimeframeOptions,
    action?: History.ActionOptions,
    provider?: string,
    language?: Language.CodeType
  ) {
    const response = await this.get<History.Stat>("/stats", {
      timeframe,
      action,
      provider,
      language,
    });
    return response;
  }
}

export default new HistoryApi();
