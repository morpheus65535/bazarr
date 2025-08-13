import plexClient from "./plexClient";

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
    return plexClient.post<PlexPinResponse>(`${this.prefix}/oauth/pin`, {});
  }

  async validateAuth(): Promise<PlexValidateResponse> {
    return plexClient.get<PlexValidateResponse>(
      `${this.prefix}/oauth/validate`,
    );
  }

  async checkPin(pinId: string): Promise<PlexPinCheckResponse> {
    return plexClient.get<PlexPinCheckResponse>(
      `${this.prefix}/oauth/pin/${pinId}/check`,
    );
  }

  async logout(): Promise<void> {
    await plexClient.post(`${this.prefix}/oauth/logout`, {});
  }

  async getServers(): Promise<PlexServersResponse> {
    return plexClient.get<PlexServersResponse>(`${this.prefix}/oauth/servers`);
  }

  async selectServer(
    request: PlexSelectServerRequest,
  ): Promise<PlexSelectedServerResponse> {
    return plexClient.post<PlexSelectedServerResponse>(
      `${this.prefix}/select-server`,
      request,
    );
  }

  async getSelectedServer(): Promise<PlexSelectedServerResponse> {
    return plexClient.get<PlexSelectedServerResponse>(
      `${this.prefix}/select-server`,
    );
  }
}

const plexApi = new PlexApi();
export default plexApi;
