import {
  FunctionComponent,
  memo,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import {
  Badge,
  Button,
  Card,
  Drawer,
  Group,
  Progress,
  ScrollArea,
  Stack,
  Text,
} from "@mantine/core";
import { faCheck, faSpinner } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { uniqueId } from "lodash";
import { NotificationItem, useNotifications } from "@/modules/task";

interface NotificationDrawerProps {
  opened: boolean;
  onClose: () => void;
}

const NotificationDrawer: FunctionComponent<NotificationDrawerProps> = ({
  opened,
  onClose,
}) => {
  const { notifications, clearNotifications } = useNotifications();

  return (
    <Drawer
      opened={opened}
      onClose={onClose}
      title="Notifications"
      position="right"
      size="md"
      padding="lg"
      withOverlay={false}
    >
      <Group p="right" mb="md">
        <Button
          variant="subtle"
          onClick={clearNotifications}
          disabled={notifications.length === 0}
        >
          Clear All
        </Button>
      </Group>

      <ScrollArea offsetScrollbars>
        {notifications.length === 0 ? (
          <Text c="dimmed" ta="center" py="xl">
            No notifications to display
          </Text>
        ) : (
          <Stack>
            {notifications.map((notification) => (
              <NotificationCard
                key={uniqueId(notification.id)}
                notification={notification}
              />
            ))}
          </Stack>
        )}
      </ScrollArea>
    </Drawer>
  );
};

const NotificationProgress = memo(
  ({ message, color }: { message: string; color?: string }) => {
    const [progress, setProgress] = useState(0);
    const messageRef = useRef(message);

    useEffect(() => {
      if (messageRef.current !== message) {
        messageRef.current = message;

        const match = message.match(/\[(\d+)\/(\d+)]/);
        if (match) {
          const current = parseInt(match[1], 10);
          const total = parseInt(match[2], 10);
          setProgress((current / total) * 100);
        } else {
          setProgress(0);
        }
      }
    }, [message]);

    return (
      <Progress value={progress} mt="sm" size="sm" color={color || "blue"} />
    );
  },
);

const NotificationContent = memo(
  ({ notification }: { notification: NotificationItem }) => {
    return (
      <>
        <Card.Section withBorder pt={12} pl={14} pb={8} pos="relative">
          <Badge
            color={notification.color || "gray"}
            pos="absolute"
            top={14}
            right={8}
          >
            {new Intl.DateTimeFormat("default", {
              hour: "numeric",
              minute: "numeric",
              second: "numeric",
            }).format(notification.timestamp)}
          </Badge>
          <Group>
            {notification.loading ? (
              <FontAwesomeIcon icon={faSpinner} spin />
            ) : (
              <FontAwesomeIcon
                icon={faCheck}
                color={notification.color || "gray"}
              />
            )}
            <Text fw={500} truncate="end" maw={250}>
              {notification.title}
            </Text>
          </Group>
        </Card.Section>

        <Text size="sm" mt="xs">
          {notification.message}
        </Text>
      </>
    );
  },
);

const NotificationCard = memo(
  ({ notification }: { notification: NotificationItem }) => {
    const processedMessage = notification.loading
      ? notification.message.replace(/\[\d+\/\d+]/, "")
      : notification.message;

    const content = useMemo(
      () => ({
        notification: {
          ...notification,
          message: processedMessage,
        },
      }),
      [notification, processedMessage],
    );

    const notificationKey = useMemo(
      () =>
        notification.id ? uniqueId(notification.id) : uniqueId("notification-"),
      [notification.id],
    );

    return (
      <Card key={notificationKey} withBorder shadow="sm" p="sm">
        <NotificationContent notification={content.notification} />

        {notification.loading && (
          <NotificationProgress
            message={notification.message}
            color={notification.color}
          />
        )}
      </Card>
    );
  },
);

export default NotificationDrawer;
