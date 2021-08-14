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
  ): Promise<History.Stat> {
    return new Promise((resolve, reject) => {
      this.get<History.Stat>("/stats", {
        timeframe,
        action,
        provider,
        language,
      })
        .then((res) => resolve(res.data))
        .catch(reject);
    });
  }
}

export default new HistoryApi();
