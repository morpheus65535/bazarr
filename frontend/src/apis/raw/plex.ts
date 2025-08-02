import BaseApi from "./base";

export interface PlexServer {
  name: string;
  address: string;
  port: string;
  uri: string;
  local: string;
  ssl: boolean;
}

export interface PlexServersResponse {
  servers: PlexServer[];
}

export interface PlexOAuthResponse {
  redirect_url?: string;
  success?: boolean;
  token?: { token: string };
  error?: string;
}

class PlexApi extends BaseApi {
  constructor() {
    super("/plex");
  }

  async startOAuth() {
    const response = await this.get<PlexOAuthResponse>("/oauth/login");
    return response;
  }

  async handleCallback(code: string) {
    const response = await this.get<PlexOAuthResponse>("/oauth/callback", {
      code,
    });
    return response;
  }

  async getServers() {
    const response = await this.get<PlexServersResponse>("/servers");
    return response;
  }

  async selectServer(server: Partial<PlexServer>) {
    const response = await this.post<{ success: boolean }>("/server", server);
    return response;
  }
}

const plexApi = new PlexApi();
export default plexApi;
