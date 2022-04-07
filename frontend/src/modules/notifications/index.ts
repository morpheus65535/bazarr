import { NotificationProps } from "@mantine/notifications";

export const notification = {
  info: (title: string, message: string): NotificationProps => {
    return {
      title,
      message,
      autoClose: 5 * 1000,
    };
  },

  warn: (title: string, message: string): NotificationProps => {
    return {
      title,
      message,
      color: "yellow",
      autoClose: 6 * 1000,
    };
  },

  PROGRESS_TIMEOUT: 10 * 1000,

  progress: (
    id: string,
    title: string,
    body: string,
    current: number,
    total: number
  ): NotificationProps & { id: string } => {
    return {
      id,
      title,
      message: `[${current}/${total}] ${body}`,
      loading: current < total,
      autoClose: 10 * 1000,
      disallowClose: current < total,
    };
  },
};
