import { useNotificationContext } from "./NotificationContext";

export function useNotifications() {
  const { notifications, clearNotifications } = useNotificationContext();

  return {
    notifications,
    clearNotifications,
  };
}
