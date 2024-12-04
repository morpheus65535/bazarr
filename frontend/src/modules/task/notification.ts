import { NotificationData } from "@mantine/notifications";

export const notification = {
  info: (title: string, message: string): NotificationData => {
    return {
      title,
      message,
      autoClose: 5 * 1000,
    };
  },

  warn: (title: string, message: string): NotificationData => {
    return {
      title,
      message,
      color: "yellow",
      autoClose: 6 * 1000,
    };
  },

  error: (title: string, message: string): NotificationData => {
    return {
      title,
      message,
      color: "red",
      autoClose: 7 * 1000,
    };
  },

  PROGRESS_TIMEOUT: 10 * 1000,

  progress: {
    pending: (
      id: string,
      header: string,
    ): NotificationData & { id: string } => {
      return {
        id,
        title: header,
        message: "Starting Tasks...",
        color: "gray",
        loading: true,
      };
    },
    update: (
      id: string,
      header: string,
      body: string,
      current: number,
      total: number,
    ): NotificationData & { id: string } => {
      return {
        id,
        title: header,
        message: `[${current}/${total}] ${body}`,
        loading: true,
        autoClose: false,
      };
    },
    end: (id: string, header: string): NotificationData & { id: string } => {
      return {
        id,
        title: header,
        message: "All Tasks Completed",
        color: "green",
        autoClose: 2 * 1000,
      };
    },
  },
};
