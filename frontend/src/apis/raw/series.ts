import { camelCaseKeys } from "@/utilities/case";
import BaseApi from "./base";
import { buildListParams } from "./utils";

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

  async seriesBy(params: Parameter.ListQuery) {
    const response = await this.get<DataWrapperWithTotal<Item.RawSeries>>(
      "",
      buildListParams(params),
    );
    return {
      ...response,
      data: response.data.map(camelCaseKeys),
    };
  }

  async modify(form: FormType.ModifyItem) {
    await this.post("", { seriesid: form.id, profileid: form.profileId });
  }

  async tags() {
    const response = await this.get<DataWrapper<{ tag: string }[]>>("/tags");
    return response.data.map(({ tag }) => tag);
  }

  async action(form: FormType.SeriesAction) {
    const payload: Record<string, unknown> = { action: form.action };

    if (form.action !== "search-wanted") {
      payload.seriesid = form.seriesId;
    }

    await this.patch("", payload);
  }

  // Starts ONE task that searches missing subtitles for every given series,
  // one after the other. The ids travel as a single comma separated field, so
  // the size of the selection isn't limited by the server's form-field cap.
  // whisperFallback: false skips the Whisper fallback for the batch; leave it
  // undefined to follow the settings.
  async searchMissingSelected(
    ids: number[],
    options?: { whisperFallback?: boolean },
  ) {
    await this.patch("", {
      action: "search-missing-selected",
      seriesids: ids.join(","),
      ...(options?.whisperFallback !== undefined && {
        whisper_fallback: options.whisperFallback,
      }),
    });
  }
}

const seriesApi = new SeriesApi();
export default seriesApi;
