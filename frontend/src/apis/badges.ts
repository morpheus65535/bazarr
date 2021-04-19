import { AxiosResponse } from "axios";
import apis from ".";

class BadgesApi {
  get<T>(path: string, params?: any): Promise<AxiosResponse<T>> {
    return apis.axios.get(`/badges${path}`, { params });
  }

  async all(): Promise<Badge> {
    return new Promise<Badge>((resolve, reject) => {
      this.get<Badge>("")
        .then((result) => {
          resolve(result.data);
        })
        .catch(reject);
    });
  }
}

export default new BadgesApi();
