import { useSystem, useSystemSettings } from "@/apis/hooks";
import { Layout } from "@/constants";
import { setSidebar } from "@/modules/redux/actions";
import { useIsOffline } from "@/modules/redux/hooks";
import { useReduxAction, useReduxStore } from "@/modules/redux/hooks/base";
import { Environment, useGotoHomepage } from "@/utilities";
import {
  faGear,
  faHeart,
  faNetworkWired,
} from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import {
  ActionIcon,
  Anchor,
  Badge,
  Burger,
  Button,
  Divider,
  Group,
  Header as MantineHeader,
  Image,
  MediaQuery,
  Menu,
  Text,
} from "@mantine/core";
import { FunctionComponent } from "react";
import { Helmet } from "react-helmet";

const Header: FunctionComponent = () => {
  const { data: settings } = useSystemSettings();
  const sidebarOpened = useReduxStore((s) => s.site.showSidebar);

  const hasLogout = (settings?.auth.type ?? "none") === "form";

  const changeSidebar = useReduxAction(setSidebar);

  const offline = useIsOffline();

  const { shutdown, restart, logout } = useSystem();

  const goHome = useGotoHomepage();

  return (
    <MantineHeader height={Layout.HEADER_HEIGHT} p="xs">
      <Helmet>
        <meta name="theme-color" content="#911f93" />
      </Helmet>
      <Group position="apart" style={{ height: "100%" }}>
        <Group>
          <MediaQuery smallerThan="sm" styles={{ display: "none" }}>
            <>
              <Image
                alt="brand"
                src={`${Environment.baseUrl}/static/logo64.png`}
                height={32}
                width={32}
                onClick={goHome}
                role="button"
              ></Image>
              <Badge size="lg" radius="sm" color="gray">
                Bazarr
              </Badge>
            </>
          </MediaQuery>
          <MediaQuery largerThan="sm" styles={{ display: "none" }}>
            <Burger
              opened={sidebarOpened}
              onClick={() => changeSidebar(!sidebarOpened)}
              size="sm"
            ></Burger>
          </MediaQuery>
        </Group>
        <Group spacing="xs" position="right">
          {/* NotificationCenter */}
          <Anchor
            href="https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=XHHRWXT9YB7WE&source=url"
            target="_blank"
          >
            <ActionIcon variant="light" color="red">
              <FontAwesomeIcon icon={faHeart}></FontAwesomeIcon>
            </ActionIcon>
          </Anchor>
          {offline ? (
            <Button color="yellow">
              <FontAwesomeIcon icon={faNetworkWired}></FontAwesomeIcon>
              <Text pl={10}>Connecting...</Text>
            </Button>
          ) : (
            <Menu
              control={
                <ActionIcon variant="light">
                  <FontAwesomeIcon icon={faGear}></FontAwesomeIcon>
                </ActionIcon>
              }
            >
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
    </MantineHeader>
  );
};

export default Header;
