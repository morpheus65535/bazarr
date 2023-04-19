import BaseApi from "./base";

class BadgesApi extends BaseApi {
  constructor() {
    super("/badges");
  }

  async all() {
    const response = await this.get<Badge>("");
    return response;
  }
}

const badgesApi = new BadgesApi();

export default badgesApi;
