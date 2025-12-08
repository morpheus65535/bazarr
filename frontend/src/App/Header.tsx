import { FunctionComponent } from "react";
import {
  Anchor,
  AppShell,
  Avatar,
  Badge,
  Burger,
  Divider,
  Group,
  Menu,
} from "@mantine/core";
import { useDisclosure } from "@mantine/hooks";
import { faBell } from "@fortawesome/free-regular-svg-icons/faBell";
import {
  faArrowRotateLeft,
  faGear,
  faPowerOff,
} from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { useSystem, useSystemJobs, useSystemSettings } from "@/apis/hooks";
import { Action, Search } from "@/components";
import { useNavbar } from "@/contexts/Navbar";
import { useIsOnline } from "@/contexts/Online";
import { Environment, useGotoHomepage } from "@/utilities";
import NotificationDrawer from "./NotificationDrawer";
import styles from "./Header.module.scss";

const AppHeader: FunctionComponent = () => {
  const { data: settings } = useSystemSettings();
  const hasLogout = settings?.auth.type === "form";

  const { show, showed } = useNavbar();

  const online = useIsOnline();
  const offline = !online;

  const { shutdown, restart, logout } = useSystem();

  const goHome = useGotoHomepage();

  const [
    jobsManagerOpened,
    { open: openJobsManager, close: closeJobsManager },
  ] = useDisclosure(false);

  const { data: jobs } = useSystemJobs();

  return (
    <AppShell.Header p="md" className={styles.header}>
      <Group justify="space-between" wrap="nowrap">
        <Group wrap="nowrap">
          <Burger
            opened={showed}
            onClick={() => show(!showed)}
            size="sm"
            hiddenFrom="sm"
          ></Burger>
          <Anchor onClick={goHome}>
            <Avatar
              alt="brand"
              size={32}
              src={`${Environment.baseUrl}/images/logo64.png`}
            ></Avatar>
          </Anchor>
          <Badge size="lg" radius="sm" variant="brand" visibleFrom="sm">
            Bazarr
          </Badge>
        </Group>
        <Group gap="xs" justify="right" wrap="nowrap">
          <Search></Search>
          <Action
            label="Jobs Manager"
            tooltip={{ position: "left", openDelay: 2000 }}
            icon={faBell}
            size="sm"
            isLoading={Boolean(
              jobs?.filter((job) => job.status === "running").length,
            )}
            onClick={openJobsManager}
          ></Action>
          <Menu>
            <Menu.Target>
              <Action
                label="System"
                tooltip={{ position: "left", openDelay: 2000 }}
                loading={offline}
                c={offline ? "yellow" : undefined}
                icon={faGear}
                size="lg"
              ></Action>
            </Menu.Target>
            <Menu.Dropdown>
              <Menu.Item
                leftSection={<FontAwesomeIcon icon={faArrowRotateLeft} />}
                onClick={() => restart()}
              >
                Restart
              </Menu.Item>
              <Menu.Item
                leftSection={<FontAwesomeIcon icon={faPowerOff} />}
                onClick={() => shutdown()}
              >
                Shutdown
              </Menu.Item>
              <Divider hidden={!hasLogout}></Divider>
              <Menu.Item hidden={!hasLogout} onClick={() => logout()}>
                Logout
              </Menu.Item>
            </Menu.Dropdown>
          </Menu>
        </Group>
      </Group>
      <NotificationDrawer
        opened={jobsManagerOpened}
        onClose={closeJobsManager}
      />
    </AppShell.Header>
  );
};

export default AppHeader;
