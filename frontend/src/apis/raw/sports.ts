import { camelCaseKeys, snakeCaseKeys } from "@/utilities/case";
import BaseApi from "./base";
import { buildListParams } from "./utils";

class SportsApi extends BaseApi {
  constructor() {
    super("/sports");
  }

  async leagues(leagueid?: number[]) {
    const response = await this.get<DataWrapperWithTotal<Item.RawSportsLeague>>(
      "/leagues",
      { leagueid },
    );
    return response.data.map(camelCaseKeys);
  }

  async leaguesBy(params: Parameter.ListQuery) {
    const response = await this.get<DataWrapperWithTotal<Item.RawSportsLeague>>(
      "/leagues",
      buildListParams(params),
    );
    return {
      ...response,
      data: response.data.map(camelCaseKeys),
    };
  }

  async modifyLeague(form: FormType.ModifyItem) {
    await this.post("/leagues", {
      leagueid: form.id,
      profileid: form.profileId,
    });
  }

  async leagueAction(form: FormType.SportsLeagueAction) {
    const payload: Record<string, unknown> = { action: form.action };

    if (form.action !== "search-wanted") {
      payload.leagueid = form.leagueId;
    }

    await this.patch("/leagues", payload);
  }

  async byLeagueId(leagueid: number[]) {
    const response = await this.get<DataWrapper<Item.RawSportsEvent[]>>(
      "/events",
      { leagueid },
    );
    return response.data.map(camelCaseKeys);
  }

  async byEventId(eventid: number[]) {
    const response = await this.get<DataWrapper<Item.RawSportsEvent[]>>(
      "/events",
      { eventid },
    );
    return response.data.map(camelCaseKeys);
  }

  async wanted(params: Parameter.Range) {
    const response = await this.get<
      DataWrapperWithTotal<Wanted.RawSportsEvent>
    >("/wanted", params);
    return {
      ...response,
      data: response.data.map(camelCaseKeys),
    };
  }

  async wantedBy(eventid: number[]) {
    const response = await this.get<
      DataWrapperWithTotal<Wanted.RawSportsEvent>
    >("/wanted", { eventid });
    return {
      ...response,
      data: response.data.map(camelCaseKeys),
    };
  }

  async history(params: Parameter.Range) {
    const response = await this.get<
      DataWrapperWithTotal<History.RawSportsEvent>
    >("/history", params);
    return camelCaseKeys(response);
  }

  async historyBy(eventid: number) {
    const response = await this.get<
      DataWrapperWithTotal<History.RawSportsEvent>
    >("/history", { eventid });
    return response.data.map(camelCaseKeys);
  }

  async blacklist() {
    const response =
      await this.get<DataWrapper<Blacklist.RawSportsEvent[]>>("/blacklist");
    return response.data.map(camelCaseKeys);
  }

  async addBlacklist(
    leagueid: number,
    eventid: number,
    form: FormType.AddBlacklist,
  ) {
    await this.post("/blacklist", snakeCaseKeys(form), { leagueid, eventid });
  }

  async deleteBlacklist(all?: boolean, form?: FormType.DeleteBlacklist) {
    await this.delete("/blacklist", snakeCaseKeys(form), { all });
  }
}

const sportsApi = new SportsApi();
export default sportsApi;
