import apis from ".";

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
  async urlTest(protocol: string, url: string, params?: any) {
    try {
      const result = await apis.axios.get<UrlTestResponse>(
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
      const result = await apis.axios.get<UrlTestResponse>(
        `../test/${protocol}/${url}api/v3/system/status`,
        { params }
      );
      return result.data;
    }
  }
}

export default new RequestUtils();
