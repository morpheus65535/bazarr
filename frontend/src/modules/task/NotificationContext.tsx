import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
} from "react";
import { NotificationData } from "@mantine/notifications";
import { setNotificationContextRef } from "./index";
import { NotificationItem } from "./notification";

interface NotificationContextType {
  notifications: NotificationItem[];
  showNotification: (
    notification: Omit<NotificationItem, "id" | "timestamp">,
  ) => void;
  updateNotification: (notification: NotificationData & { id: string }) => void;
  hideNotification: (id: string) => void;
  clearNotifications: () => void;
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
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);

  const showNotification = useCallback(
    (notification: NotificationData & { id?: string }) => {
      const newNotification = {
        ...notification,
        title: String(notification.title),
        message: String(notification.message),
        id: notification.id ?? `notification-${Date.now()}`,
        timestamp: new Date(),
      };

      setNotifications((prev) => [...prev, newNotification]);
    },
    [],
  );

  const updateNotification = useCallback(
    (notification: NotificationData & { id: string }) => {
      if (notification.id) {
        setNotifications((prev) => {
          const existing = prev.findIndex((n) => n.id === notification.id);
          if (existing >= 0) {
            const updated = [...prev];
            updated[existing] = {
              ...notification,
              title: String(notification.title),
              message: String(notification.message),
              timestamp: new Date(),
            };
            return updated;
          }
          return [
            ...prev,
            {
              ...notification,
              title: String(notification.title),
              message: String(notification.message),
              timestamp: new Date(),
            },
          ];
        });
      }
    },
    [],
  );

  const hideNotification = useCallback((id: string) => {
    setNotifications((prev) =>
      prev.filter((notification) => notification.id !== id),
    );
  }, []);

  const clearNotifications = useCallback(() => {
    setNotifications([]);
  }, []);

  useEffect(() => {
    setNotificationContextRef(
      showNotification,
      updateNotification,
      hideNotification,
    );
  }, [showNotification, updateNotification, hideNotification]);

  const sortedNotifications = [...notifications].sort(
    (a, b) => b.timestamp.getTime() - a.timestamp.getTime(),
  );

  const value = {
    notifications: sortedNotifications,
    showNotification,
    updateNotification,
    hideNotification,
    clearNotifications,
  };

  return (
    <NotificationContext.Provider value={value}>
      {children}
    </NotificationContext.Provider>
  );
};
