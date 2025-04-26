export { useNotifications } from "./hooks";

export interface NotificationItem {
  id?: string;
  title: string;
  message: string;
  color?: string;
  loading?: boolean;
  timestamp: number;
  progress?: {
    current: number;
    total: number;
  };
}

export const notification = {
  info: (title: string, message: string): NotificationItem => {
    return {
      timestamp: new Date().getTime(),
      title,
      message,
    };
  },

  warn: (title: string, message: string): NotificationItem => {
    return {
      title,
      message,
      color: "yellow",
      timestamp: new Date().getTime(),
    };
  },

  error: (title: string, message: string): NotificationItem => {
    return {
      title,
      message,
      color: "red",
      timestamp: new Date().getTime(),
    };
  },

  PROGRESS_TIMEOUT: 10 * 1000,

  progress: {
    pending: (id: string, header: string): NotificationItem => {
      return {
        id,
        title: header,
        message: "Starting Tasks...",
        color: "gray",
        loading: true,
        timestamp: new Date().getTime(),
      };
    },
    update: (
      id: string,
      header: string,
      body: string,
      current: number,
      total: number,
    ): NotificationItem => {
      return {
        id,
        title: header,
        message: `[${current}/${total}] ${body}`,
        progress: {
          current,
          total,
        },
        loading: true,
        timestamp: new Date().getTime(),
      };
    },
    end: (id: string, header: string): NotificationItem => {
      return {
        id,
        title: header,
        message: "All Tasks Completed",
        color: "green",
        timestamp: new Date().getTime(),
      };
    },
  },
};
