import Axios, { type AxiosError, type AxiosInstance } from "axios";
import { PLEX_ERROR_CODES, type PlexErrorCode } from "@/constants/plex";
import { Environment } from "@/utilities";
import { createPlexError } from "@/utilities/plexErrors";

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

    this.axios.interceptors.response.use(
      (response) => response,
      (error: AxiosError) => {
        const responseData = error.response?.data as {
          error?: string;
          code?: string;
        };
        const errorCode =
          responseData?.code || PLEX_ERROR_CODES.CONNECTION_ERROR;
        const errorMessage =
          responseData?.error || error.message || "An unknown error occurred";

        const plexError = createPlexError(
          errorMessage,
          errorCode as PlexErrorCode,
          error.response?.status ? error.response.status >= 500 : false,
        );

        return Promise.reject(plexError);
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
