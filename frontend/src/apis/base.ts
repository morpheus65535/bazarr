import { AxiosResponse } from "axios";
import apis from ".";

class BaseApi {
  prefix: string;

  constructor(prefix: string) {
    this.prefix = prefix;
  }

  private createFormdata(object?: LooseObject) {
    if (object) {
      let form = new FormData();

      for (const key in object) {
        const data = object[key];
        if (data instanceof Array) {
          if (data.length > 0) {
            data.forEach((val) => form.append(key, val));
          } else {
            form.append(key, "");
          }
        } else {
          form.append(key, object[key]);
        }
      }
      return form;
    } else {
      return undefined;
    }
  }

  protected async get<T = unknown>(path: string, params?: any) {
    const response = await apis.axios.get<T>(this.prefix + path, { params });
    return response.data;
  }

  protected post<T = void>(
    path: string,
    formdata?: LooseObject,
    params?: any
  ): Promise<AxiosResponse<T>> {
    const form = this.createFormdata(formdata);
    return apis.axios.post(this.prefix + path, form, { params });
  }

  protected patch<T = void>(
    path: string,
    formdata?: LooseObject,
    params?: any
  ): Promise<AxiosResponse<T>> {
    const form = this.createFormdata(formdata);
    return apis.axios.patch(this.prefix + path, form, { params });
  }

  protected delete<T = void>(
    path: string,
    formdata?: any,
    params?: any
  ): Promise<AxiosResponse<T>> {
    const form = this.createFormdata(formdata);
    return apis.axios.delete(this.prefix + path, { params, data: form });
  }
}

export default BaseApi;
