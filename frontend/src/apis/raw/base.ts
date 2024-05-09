import { AxiosResponse } from "axios";
import client from "./client";

class BaseApi {
  prefix: string;

  constructor(prefix: string) {
    this.prefix = prefix;
  }

  private createFormdata(object?: LooseObject) {
    if (object) {
      const form = new FormData();

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

  protected async get<T = unknown>(path: string, params?: LooseObject) {
    const response = await client.axios.get<T>(this.prefix + path, { params });
    return response.data;
  }

  protected post<T = void>(
    path: string,
    formdata?: LooseObject,
    params?: LooseObject,
  ): Promise<AxiosResponse<T>> {
    const form = this.createFormdata(formdata);
    return client.axios.post(this.prefix + path, form, {
      params,
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
    });
  }

  protected patch<T = void>(
    path: string,
    formdata?: LooseObject,
    params?: LooseObject,
  ): Promise<AxiosResponse<T>> {
    const form = this.createFormdata(formdata);
    return client.axios.patch(this.prefix + path, form, { params });
  }

  protected delete<T = void>(
    path: string,
    formdata?: LooseObject,
    params?: LooseObject,
  ): Promise<AxiosResponse<T>> {
    const form = this.createFormdata(formdata);
    return client.axios.delete(this.prefix + path, { params, data: form });
  }
}

export default BaseApi;
