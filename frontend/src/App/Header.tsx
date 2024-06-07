import { useSystem, useSystemSettings } from "@/apis/hooks";
import { Action, Search } from "@/components";
import { useNavbar } from "@/contexts/Navbar";
import { useIsOnline } from "@/contexts/Online";
import { Environment, useGotoHomepage } from "@/utilities";
import {
  faArrowRotateLeft,
  faGear,
  faPowerOff,
} from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
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
import { FunctionComponent } from "react";
import styles from "./Header.module.scss";

const AppHeader: FunctionComponent = () => {
  const { data: settings } = useSystemSettings();
  const hasLogout = settings?.auth.type === "form";

  const { show, showed } = useNavbar();

  const online = useIsOnline();
  const offline = !online;

  const { shutdown, restart, logout } = useSystem();

  const goHome = useGotoHomepage();

  return (
    <AppShell.Header p="md" className={styles.header}>
      <Group justify="space-between" wrap="nowrap">
        <Group wrap="nowrap">
          <Anchor onClick={goHome} visibleFrom="sm">
            <Avatar
              alt="brand"
              size={32}
              src={`${Environment.baseUrl}/images/logo64.png`}
            ></Avatar>
          </Anchor>
          <Burger
            opened={showed}
            onClick={() => show(!showed)}
            size="sm"
            hiddenFrom="sm"
          ></Burger>
          <Badge size="lg" radius="sm" variant="brand">
            Bazarr
          </Badge>
        </Group>
        <Group gap="xs" justify="right" wrap="nowrap">
          <Search></Search>
          <Menu>
            <Menu.Target>
              <Action
                label="System"
                tooltip={{ position: "left", openDelay: 2000 }}
                loading={offline}
                color={offline ? "yellow" : undefined}
                icon={faGear}
                size="lg"
                variant="light"
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
    </AppShell.Header>
  );
};

export default AppHeader;
