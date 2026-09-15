import { AxiosResponse } from "axios";
import client from "./client";

class BaseApi {
  prefix: string;

  constructor(prefix: string) {
    this.prefix = prefix;
  }

  private createFormdata(object?: unknown) {
    const record = object as Record<string, unknown> | undefined;
    if (record) {
      const form = new FormData();

      for (const key in record) {
        const data = record[key];
        if (data instanceof Array) {
          if (data.length > 0) {
            data.forEach((val) => form.append(key, val as string | Blob));
          } else {
            form.append(key, "");
          }
        } else {
          form.append(key, data as string | Blob);
        }
      }
      return form;
    } else {
      return undefined;
    }
  }

  protected async get<T = unknown>(path: string, params?: unknown) {
    const response = await client.axios.get<T>(this.prefix + path, {
      params: params as Record<string, unknown> | undefined,
    });
    return response.data;
  }

  protected post<T = void>(
    path: string,
    formdata?: unknown,
    params?: unknown,
  ): Promise<AxiosResponse<T>> {
    const form = this.createFormdata(formdata);
    return client.axios.post(this.prefix + path, form, {
      params: params as Record<string, unknown> | undefined,
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
    });
  }

  protected patch<T = void>(
    path: string,
    formdata?: unknown,
    params?: unknown,
  ): Promise<AxiosResponse<T>> {
    const form = this.createFormdata(formdata);
    return client.axios.patch(this.prefix + path, form, {
      params: params as Record<string, unknown> | undefined,
    });
  }

  protected delete<T = void>(
    path: string,
    formdata?: unknown,
    params?: unknown,
  ): Promise<AxiosResponse<T>> {
    const form = this.createFormdata(formdata);
    return client.axios.delete(this.prefix + path, {
      params: params as Record<string, unknown> | undefined,
      data: form,
    });
  }
}

export default BaseApi;
