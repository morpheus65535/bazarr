import { useNotificationContext } from "./NotificationContext";

export function useNotifications() {
  const { notifications, clearNotifications, markAsRead } =
    useNotificationContext();

  return {
    notifications,
    clearNotifications,
    markAsRead,
  };
}
