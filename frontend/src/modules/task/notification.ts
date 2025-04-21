import { NotificationData } from "@mantine/notifications";

const defaultPosition = "bottom-left";

export const notification = {
  info: (title: string, message: string): NotificationData => {
    return {
      title,
      message,
      autoClose: 5 * 1000,
      position: defaultPosition,
    };
  },

  warn: (title: string, message: string): NotificationData => {
    return {
      title,
      message,
      color: "yellow",
      autoClose: 6 * 1000,
      position: defaultPosition,
    };
  },

  error: (title: string, message: string): NotificationData => {
    return {
      title,
      message,
      color: "red",
      autoClose: 7 * 1000,
      position: defaultPosition,
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
        position: defaultPosition,
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
        position: defaultPosition,
      };
    },
    end: (id: string, header: string): NotificationData & { id: string } => {
      return {
        id,
        title: header,
        message: "All Tasks Completed",
        color: "green",
        autoClose: 2 * 1000,
        position: defaultPosition,
      };
    },
  },
};
