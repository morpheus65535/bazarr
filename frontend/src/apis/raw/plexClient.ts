import Axios, { AxiosError, AxiosInstance } from "axios";
import { Environment } from "@/utilities";

/**
 * Dedicated Plex API client that doesn't interfere with main Bazarr authentication
 */
class PlexApiClient {
  private axios: AxiosInstance;

  constructor() {
    const baseUrl = `${Environment.baseUrl}/api/`;

    this.axios = Axios.create({
      baseURL: baseUrl,
      headers: {
        "Content-Type": "application/json",
        "X-API-KEY": Environment.apiKey ?? "AUTH_NEEDED",
      },
    });

    // Custom error handling that doesn't affect global auth state
    this.axios.interceptors.response.use(
      (response) => response,
      (error: AxiosError) => {
        // Just pass through the error without global side effects
        return Promise.reject(error);
      },
    );
  }

  async get<T>(url: string): Promise<T> {
    const response = await this.axios.get<T>(url);
    return response.data;
  }

  async post<T>(url: string, data?: unknown): Promise<T> {
    const response = await this.axios.post<T>(url, data);
    return response.data;
  }
}

const plexClient = new PlexApiClient();
export default plexClient;
