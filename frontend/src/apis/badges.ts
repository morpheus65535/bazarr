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

export default new BadgesApi();
