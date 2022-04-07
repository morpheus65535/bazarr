import { useSystem, useSystemSettings } from "@/apis/hooks";
import { Action } from "@/components";
import { Layout } from "@/constants";
import { setSidebar } from "@/modules/redux/actions";
import { useIsOffline } from "@/modules/redux/hooks";
import { useReduxAction, useReduxStore } from "@/modules/redux/hooks/base";
import { Environment, useGotoHomepage } from "@/utilities";
import { faGear, faNetworkWired } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import {
  Anchor,
  Avatar,
  Badge,
  Burger,
  Button,
  Divider,
  Group,
  Header,
  MediaQuery,
  Menu,
  Text,
} from "@mantine/core";
import { FunctionComponent } from "react";
import { Helmet } from "react-helmet";

const AppHeader: FunctionComponent = () => {
  const { data: settings } = useSystemSettings();
  const sidebarOpened = useReduxStore((s) => s.site.showSidebar);

  const hasLogout = (settings?.auth.type ?? "none") === "form";

  const changeSidebar = useReduxAction(setSidebar);

  const offline = useIsOffline();

  const { shutdown, restart, logout } = useSystem();

  const goHome = useGotoHomepage();

  return (
    <Header p="md" height={Layout.HEADER_HEIGHT}>
      <Helmet>
        <meta name="theme-color" content="#911f93" />
      </Helmet>
      <Group position="apart">
        <Group>
          <MediaQuery
            smallerThan={Layout.MOBILE_BREAKPOINT}
            styles={{ display: "none" }}
          >
            <Anchor onClick={goHome}>
              <Avatar
                alt="brand"
                size={32}
                src={`${Environment.baseUrl}/static/logo64.png`}
              ></Avatar>
            </Anchor>
          </MediaQuery>
          <MediaQuery
            largerThan={Layout.MOBILE_BREAKPOINT}
            styles={{ display: "none" }}
          >
            <Burger
              opened={sidebarOpened}
              onClick={() => changeSidebar(!sidebarOpened)}
              size="sm"
            ></Burger>
          </MediaQuery>
          <Badge size="lg" radius="sm" color="gray">
            Bazarr
          </Badge>
        </Group>
        <Group spacing="xs" position="right">
          {/* NotificationCenter */}
          {offline ? (
            <Button color="yellow">
              <FontAwesomeIcon icon={faNetworkWired}></FontAwesomeIcon>
              <Text pl={10}>Connecting...</Text>
            </Button>
          ) : (
            <Menu control={<Action icon={faGear} variant="light"></Action>}>
              <Menu.Item onClick={() => restart()}>Restart</Menu.Item>
              <Menu.Item onClick={() => shutdown()}>Shutdown</Menu.Item>
              <Divider></Divider>
              <Menu.Item hidden={!hasLogout} onClick={() => logout()}>
                Logout
              </Menu.Item>
            </Menu>
          )}
        </Group>
      </Group>
    </Header>
  );
};

export default AppHeader;
