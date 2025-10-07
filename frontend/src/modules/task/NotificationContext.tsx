import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
} from "react";
import { useLocalStorage } from "@mantine/hooks";
import { setNotificationContextRef } from "./index";
import { NotificationItem } from "./notification";

const MAX_NOTIFICATIONS = 100;

interface NotificationContextType {
  notifications: NotificationItem[];
  showNotification: (notification: NotificationItem) => void;
  updateNotification: (notification: NotificationItem) => void;
  hideNotification: (id: string) => void;
  clearNotifications: () => void;
  markAsRead: () => void;
}

const NotificationContext = createContext<NotificationContextType | undefined>(
  undefined,
);

export const useNotificationContext = (): NotificationContextType => {
  const context = useContext(NotificationContext);
  if (context === undefined) {
    throw new Error(
      "useNotificationContext must be used within a NotificationProvider",
    );
  }
  return context;
};

export const NotificationProvider: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  const [notifications, setNotifications] = useLocalStorage<NotificationItem[]>(
    {
      key: "notifications",
      defaultValue: [],
    },
  );

  const showNotification = useCallback(
    (notification: NotificationItem) => {
      const newNotification = {
        ...notification,
        title: String(notification.title),
        message: String(notification.message),
        id: notification.id ?? `notification-${Date.now()}`,
        timestamp: notification.timestamp ?? new Date().getTime(),
      };

      setNotifications((prev) => {
        const updated = [...prev, newNotification];
        return updated.length > MAX_NOTIFICATIONS
          ? updated.slice(-MAX_NOTIFICATIONS)
          : updated;
      });
    },
    [setNotifications],
  );

  const updateNotification = useCallback(
    (notification: NotificationItem) => {
      if (notification.id) {
        setNotifications((prev) => {
          const existing = prev.findIndex((n) => n.id === notification.id);
          if (existing >= 0) {
            const updated = [...prev];
            updated[existing] = {
              ...notification,
              title: String(notification.title),
              message: String(notification.message),
              timestamp: prev[existing].timestamp,
            };
            return updated;
          }
          return [
            ...prev,
            {
              ...notification,
              title: String(notification.title),
              message: String(notification.message),
              timestamp: notification.timestamp ?? new Date().getTime(),
            },
          ];
        });
      }
    },
    [setNotifications],
  );

  const hideNotification = useCallback(
    (id: string) => {
      setNotifications((prev) =>
        prev.filter((notification) => notification.id !== id),
      );
    },
    [setNotifications],
  );

  const clearNotifications = useCallback(() => {
    setNotifications([]);
  }, [setNotifications]);

  const markAsRead = useCallback(() => {
    setNotifications((prev) =>
      prev.map((notification) => ({
        ...notification,
        read: true,
      })),
    );
  }, [setNotifications]);

  // Set context ref in useEffect with proper dependencies
  useEffect(() => {
    setNotificationContextRef(
      showNotification,
      updateNotification,
      hideNotification,
      markAsRead,
    );
  }, [showNotification, updateNotification, hideNotification, markAsRead]);

  const sortedNotifications = [...notifications].sort((a, b) => {
    if (a.loading && !b.loading) return -1;
    if (!a.loading && b.loading) return 1;
    return 0; // Equal elements preserve their order
  });

  const value = {
    notifications: sortedNotifications,
    showNotification,
    updateNotification,
    hideNotification,
    clearNotifications,
    markAsRead,
  };

  return (
    <NotificationContext.Provider value={value}>
      {children}
    </NotificationContext.Provider>
  );
};
