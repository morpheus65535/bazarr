import client from "./client";

type UrlTestResponse =
  | {
      status: true;
      version: string;
    }
  | {
      status: false;
      error: string;
    };

class RequestUtils {
  async urlTest(protocol: string, url: string, params?: LooseObject) {
    try {
      const result = await client.axios.get<UrlTestResponse>(
        `../test/${protocol}/${url}api/system/status`,
        { params }
      );
      const { data } = result;
      if (data.status && data.version) {
        return data;
      } else {
        throw new Error("Cannot get response, fallback to v3 api");
      }
    } catch (e) {
      const result = await client.axios.get<UrlTestResponse>(
        `../test/${protocol}/${url}api/v3/system/status`,
        { params }
      );
      return result.data;
    }
  }
}

export default new RequestUtils();
