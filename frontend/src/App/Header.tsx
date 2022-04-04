import { useSystem, useSystemSettings } from "@/apis/hooks";
import { SearchBar } from "@/components";
import { setSidebar } from "@/modules/redux/actions";
import { useIsOffline } from "@/modules/redux/hooks";
import { useReduxAction } from "@/modules/redux/hooks/base";
import { Environment, useGotoHomepage, useIsMobile } from "@/utilities";
import {
  faBars,
  faHeart,
  faNetworkWired,
} from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import {
  Anchor,
  Button,
  Divider,
  Grid,
  Group,
  Image,
  Menu,
  Navbar,
} from "@mantine/core";
import { FunctionComponent } from "react";
import { Helmet } from "react-helmet";

const Header: FunctionComponent = () => {
  const { data: settings } = useSystemSettings();

  const hasLogout = (settings?.auth.type ?? "none") === "form";

  const changeSidebar = useReduxAction(setSidebar);

  const offline = useIsOffline();

  const isMobile = useIsMobile();

  const { shutdown, restart, logout } = useSystem();

  const serverActions = (
    <Menu>
      <Menu.Item>Restart</Menu.Item>
      <Menu.Item>Shutdown</Menu.Item>
      <Divider></Divider>
      <Menu.Item>Logout</Menu.Item>
    </Menu>
    // <Dropdown alignRight>
    //   <Dropdown.Toggle className="hide-arrow" as={Button}>
    //     <FontAwesomeIcon icon={faUser}></FontAwesomeIcon>
    //   </Dropdown.Toggle>
    //   <Dropdown.Menu>
    //     <Dropdown.Item
    //       onClick={() => {
    //         restart();
    //       }}
    //     >
    //       Restart
    //     </Dropdown.Item>
    //     <Dropdown.Item
    //       onClick={() => {
    //         shutdown();
    //       }}
    //     >
    //       Shutdown
    //     </Dropdown.Item>
    //     <Dropdown.Divider hidden={!hasLogout}></Dropdown.Divider>
    //     <Dropdown.Item
    //       hidden={!hasLogout}
    //       onClick={() => {
    //         logout();
    //       }}
    //     >
    //       Logout
    //     </Dropdown.Item>
    //   </Dropdown.Menu>
    // </Dropdown>
  );

  const goHome = useGotoHomepage();

  return (
    <Navbar>
      <Helmet>
        <meta name="theme-color" content="#911f93" />
      </Helmet>
      <div className="header-icon px-3 m-0 d-none d-md-block">
        <Image
          alt="brand"
          src={`${Environment.baseUrl}/static/logo64.png`}
          width="32"
          height="32"
          onClick={goHome}
          role="button"
        ></Image>
      </div>
      <Button
        className="mx-2 m-0 d-md-none"
        onClick={() => changeSidebar(true)}
      >
        <FontAwesomeIcon icon={faBars}></FontAwesomeIcon>
      </Button>
      <Grid>
        <Grid.Col span={6} xs={4}>
          <SearchBar></SearchBar>
        </Grid.Col>
        <Grid.Col span={6} xs={4}>
          <Group>
            {/* NotificationCenter */}
            <Anchor
              href="https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=XHHRWXT9YB7WE&source=url"
              target="_blank"
            >
              <FontAwesomeIcon icon={faHeart}></FontAwesomeIcon>
            </Anchor>
            {offline ? (
              <Button color="yellow">
                <FontAwesomeIcon icon={faNetworkWired}></FontAwesomeIcon>
                Connecting...
              </Button>
            ) : (
              serverActions
            )}
          </Group>
        </Grid.Col>
      </Grid>
    </Navbar>
  );
};

export default Header;
