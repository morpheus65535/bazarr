import SocketIO from "@/modules/socketio";
import { notification } from "@/modules/task";
import { LOG } from "@/utilities/console";
import { setLoginRequired } from "@/utilities/event";
import { showNotification } from "@mantine/notifications";
import Axios, { AxiosError, AxiosInstance, CancelTokenSource } from "axios";
import { Environment } from "../../utilities";

function GetErrorMessage(data: unknown, defaultMsg = "Unknown error"): string {
  if (typeof data === "string") {
    return data;
  } else {
    return defaultMsg;
  }
}

class BazarrClient {
  axios!: AxiosInstance;
  source!: CancelTokenSource;

  constructor() {
    const baseUrl = `${Environment.baseUrl}/api/`;

    LOG("info", "initializing BazarrClient with", baseUrl);

    this.initialize(baseUrl, Environment.apiKey);
    SocketIO.initialize();
  }

  initialize(url: string, apikey?: string) {
    this.axios = Axios.create({
      baseURL: url,
    });

    this.axios.defaults.headers.post["Content-Type"] = "application/json";
    this.axios.defaults.headers.common["X-API-KEY"] = apikey ?? "AUTH_NEEDED";

    this.source = Axios.CancelToken.source();

    this.axios.interceptors.request.use((config) => {
      config.cancelToken = this.source.token;
      return config;
    });

    this.axios.interceptors.response.use(
      (resp) => {
        if (resp.status >= 200 && resp.status < 300) {
          return Promise.resolve(resp);
        } else {
          const error: BackendError = {
            code: resp.status,
            message: GetErrorMessage(resp.data),
          };
          this.handleError(error);
          return Promise.reject(resp);
        }
      },
      (error: AxiosError) => {
        const message = GetErrorMessage(
          error.response?.data,
          "You have disconnected from the server"
        );

        const backendError: BackendError = {
          code: error.response?.status ?? 500,
          message,
        };

        error.message = backendError.message;
        this.handleError(backendError);

        return Promise.reject(error);
      }
    );
  }

  handleError(error: BackendError) {
    const { code, message } = error;
    switch (code) {
      case 401:
        setLoginRequired();
        return;
    }
    LOG("error", "A error has occurred", code);

    showNotification(notification.error(`Error ${code}`, message));
  }
}

export default new BazarrClient();
