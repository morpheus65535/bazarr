import { AxiosResponse } from "axios";
import apis from ".";

class BasicApi {
  prefix: string;

  constructor(prefix: string) {
    this.prefix = prefix;
  }

  protected get<T>(path: string, params?: any): Promise<AxiosResponse<T>> {
    return apis.axios.get(this.prefix + path, { params });
  }

  protected post<T>(
    path: string,
    form?: any,
    params?: any
  ): Promise<AxiosResponse<T>> {
    return apis.post(this.prefix + path, form, params);
  }

  protected patch<T>(
    path: string,
    form?: any,
    params?: any
  ): Promise<AxiosResponse<T>> {
    return apis.patch(this.prefix + path, form, params);
  }

  protected delete<T>(
    path: string,
    form?: any,
    params?: any
  ): Promise<AxiosResponse<T>> {
    return apis.delete(this.prefix + path, form, params);
  }
}

export default BasicApi;
