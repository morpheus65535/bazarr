import BaseApi from "./base";

interface JellyfinTestResult {
  success: boolean;
  server_name?: string;
  version?: string;
  error?: string;
}

interface JellyfinLibrary {
  id: string;
  name: string;
  type: string;
}

class JellyfinApi extends BaseApi {
  constructor() {
    super("/jellyfin");
  }

  async testConnection(url: string, apikey: string) {
    const response = await this.post<JellyfinTestResult>("/test-connection", {
      url,
      apikey,
    });

    return response.data;
  }

  async libraries(url?: string, apikey?: string) {
    const params: Record<string, string> = {};
    if (url) params.url = url;
    if (apikey) params.apikey = apikey;

    const response = await this.get<{ data: JellyfinLibrary[] }>(
      "/libraries",
      params,
    );

    return response.data;
  }
}

export default new JellyfinApi();
