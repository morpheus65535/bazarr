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

  protected get<T>(path: string, params?: any): Promise<AxiosResponse<T>> {
    return apis.axios.get(this.prefix + path, { params });
  }

  protected post<T>(
    path: string,
    formdata?: LooseObject,
    params?: any
  ): Promise<AxiosResponse<T>> {
    const form = this.createFormdata(formdata);
    return apis.axios.post(this.prefix + path, form, { params });
  }

  protected patch<T>(
    path: string,
    formdata?: LooseObject,
    params?: any
  ): Promise<AxiosResponse<T>> {
    const form = this.createFormdata(formdata);
    return apis.axios.patch(this.prefix + path, form, { params });
  }

  protected delete<T>(
    path: string,
    formdata?: any,
    params?: any
  ): Promise<AxiosResponse<T>> {
    const form = this.createFormdata(formdata);
    return apis.axios.delete(this.prefix + path, { params, data: form });
  }
}

export default BaseApi;
