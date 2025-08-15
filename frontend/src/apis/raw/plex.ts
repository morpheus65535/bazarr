import client from "./client";

export interface PlexPinResponse {
  pinId: string;
  code: string;
  clientId: string;
  authUrl: string;
}

export interface PlexValidateResponse {
  valid: boolean;
  auth_method?: string;
  username?: string;
  email?: string;
  error?: string;
  code?: string;
}

export interface PlexPinCheckResponse {
  authenticated: boolean;
  username?: string;
  email?: string;
  error?: string;
}

export interface PlexServerConnection {
  uri: string;
  protocol: string;
  address: string;
  port: number;
  local: boolean;
  available?: boolean;
  latency?: number;
}

export interface PlexServer {
  name: string;
  machineIdentifier: string;
  connections: PlexServerConnection[];
  version: string;
  platform: string;
  device: string;
  bestConnection?: PlexServerConnection | null;
}

export interface PlexServersResponse {
  servers: PlexServer[];
}

export interface PlexSelectServerRequest {
  machineIdentifier: string;
  name: string;
  connection: {
    uri: string;
    local: boolean;
  };
}

export interface PlexSelectedServerResponse {
  server: PlexServer;
}

class PlexApi {
  private prefix: string;

  constructor() {
    this.prefix = "/plex";
  }

  async createPin(): Promise<PlexPinResponse> {
    const response = await client.axios.post<PlexPinResponse>(
      `${this.prefix}/oauth/pin`,
      {},
    );
    return response.data;
  }

  async validateAuth(): Promise<PlexValidateResponse> {
    const response = await client.axios.get<PlexValidateResponse>(
      `${this.prefix}/oauth/validate`,
    );
    return response.data;
  }

  async checkPin(pinId: string): Promise<PlexPinCheckResponse> {
    const response = await client.axios.get<PlexPinCheckResponse>(
      `${this.prefix}/oauth/pin/${pinId}/check`,
    );
    return response.data;
  }

  async logout(): Promise<void> {
    await client.axios.post(`${this.prefix}/oauth/logout`, {});
  }

  async getServers(): Promise<PlexServersResponse> {
    const response = await client.axios.get<PlexServersResponse>(
      `${this.prefix}/oauth/servers`,
    );
    return response.data;
  }

  async selectServer(
    request: PlexSelectServerRequest,
  ): Promise<PlexSelectedServerResponse> {
    const response = await client.axios.post<PlexSelectedServerResponse>(
      `${this.prefix}/select-server`,
      request,
    );
    return response.data;
  }

  async getSelectedServer(): Promise<PlexSelectedServerResponse> {
    const response = await client.axios.get<PlexSelectedServerResponse>(
      `${this.prefix}/select-server`,
    );
    return response.data;
  }
}

const plexApi = new PlexApi();
export default plexApi;
