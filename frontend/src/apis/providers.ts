import { AxiosResponse } from "axios";
import apis from ".";

class ProviderApi {
  get<T>(path: string, params?: any): Promise<AxiosResponse<T>> {
    return apis.axios.get(`/providers${path}`, { params });
  }

  async providers() {
    return new Promise<Array<SystemProvider>>((resolve, reject) => {
      this.get<DataWrapper<Array<SystemProvider>>>("")
        .then((result) => {
          resolve(result.data.data);
        })
        .catch(reject);
    });
  }
}

export default new ProviderApi();
