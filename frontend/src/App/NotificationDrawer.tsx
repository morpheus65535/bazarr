import { FunctionComponent } from "react";
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
import { useNotifications } from "@/modules/task";

interface NotificationDrawerProps {
  opened: boolean;
  onClose: () => void;
}

const NotificationDrawer: FunctionComponent<NotificationDrawerProps> = ({
  opened,
  onClose,
}) => {
  const { notifications, clearNotifications } = useNotifications();

  const getProgressFromMessage = (message: string) => {
    const match = message.match(/\[(\d+)\/(\d+)]/);
    if (match) {
      const current = parseInt(match[1], 10);
      const total = parseInt(match[2], 10);
      return (current / total) * 100;
    }
    return 0;
  };

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

      <ScrollArea h="calc(100vh - 130px)" offsetScrollbars>
        {notifications.length === 0 ? (
          <Text c="dimmed" ta="center" py="xl">
            No notifications to display
          </Text>
        ) : (
          <Stack>
            {notifications.map((notification) => (
              <Card key={notification.id} withBorder shadow="sm" p="sm">
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
                      <FontAwesomeIcon icon={faSpinner} />
                    ) : (
                      <FontAwesomeIcon
                        icon={faCheck}
                        color={notification.color || "gray"}
                      />
                    )}
                    <Text fw={500}>{notification.title}</Text>
                  </Group>
                </Card.Section>

                <Text size="sm" mt="xs">
                  {notification.message}
                </Text>

                {notification.loading && (
                  <Progress
                    value={getProgressFromMessage(notification.message)}
                    mt="sm"
                    size="sm"
                    color={notification.color || "blue"}
                  />
                )}
              </Card>
            ))}
          </Stack>
        )}
      </ScrollArea>
    </Drawer>
  );
};

export default NotificationDrawer;
