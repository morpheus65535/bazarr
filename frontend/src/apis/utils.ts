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
  urlTest(
    protocol: string,
    url: string,
    params?: any
  ): Promise<UrlTestResponse> {
    return new Promise<UrlTestResponse>((resolve, reject) => {
      apis.axios
        .get(`../test/${protocol}/${url}api/system/status`, { params })
        .then((result) => resolve(result.data))
        .catch(reject);
    });
  }
}

export default new RequestUtils();
