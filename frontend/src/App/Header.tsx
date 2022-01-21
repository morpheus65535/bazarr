import {
  faBars,
  faHeart,
  faNetworkWired,
  faUser,
} from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import React, { FunctionComponent, useMemo } from "react";
import {
  Button,
  Col,
  Container,
  Dropdown,
  Image,
  Navbar,
  Row,
} from "react-bootstrap";
import { Helmet } from "react-helmet";
import api from "src/apis/raw";
import {
  siteChangeSidebarVisibility,
  siteRedirectToAuth,
} from "../@redux/actions";
import { useIsOffline } from "../@redux/hooks";
import { useReduxAction } from "../@redux/hooks/base";
import logo from "../@static/logo64.png";
import { useSystemSettings } from "../apis/queries/client";
import { ActionButton, SearchBar } from "../components";
import { useGotoHomepage, useIsMobile } from "../utilities";
import "./header.scss";
import NotificationCenter from "./Notification";

interface Props {}

const Header: FunctionComponent<Props> = () => {
  const setNeedAuth = useReduxAction(siteRedirectToAuth);

  const { data: settings } = useSystemSettings();

  const canLogout = (settings?.auth.type ?? "none") === "form";

  const changeSidebar = useReduxAction(siteChangeSidebarVisibility);

  const offline = useIsOffline();

  const isMobile = useIsMobile();

  const serverActions = useMemo(
    () => (
      <Dropdown alignRight>
        <Dropdown.Toggle className="dropdown-hidden" as={Button}>
          <FontAwesomeIcon icon={faUser}></FontAwesomeIcon>
        </Dropdown.Toggle>
        <Dropdown.Menu>
          <Dropdown.Item
            onClick={() => {
              api.system.restart();
            }}
          >
            Restart
          </Dropdown.Item>
          <Dropdown.Item
            onClick={() => {
              api.system.shutdown();
            }}
          >
            Shutdown
          </Dropdown.Item>
          <Dropdown.Divider hidden={!canLogout}></Dropdown.Divider>
          <Dropdown.Item
            hidden={!canLogout}
            onClick={() => {
              api.system.logout().then(() => setNeedAuth());
            }}
          >
            Logout
          </Dropdown.Item>
        </Dropdown.Menu>
      </Dropdown>
    ),
    [canLogout, setNeedAuth]
  );

  const goHome = useGotoHomepage();

  return (
    <Navbar bg="primary" className="flex-grow-1 px-0">
      <Helmet>
        <meta name="theme-color" content="#911f93" />
      </Helmet>
      <div className="header-icon px-3 m-0 d-none d-md-block">
        <Image
          alt="brand"
          src={logo}
          width="32"
          height="32"
          onClick={goHome}
          className="cursor-pointer"
        ></Image>
      </div>
      <Button
        className="mx-2 m-0 d-md-none"
        onClick={() => changeSidebar(true)}
      >
        <FontAwesomeIcon icon={faBars}></FontAwesomeIcon>
      </Button>
      <Container fluid>
        <Row noGutters className="flex-grow-1">
          <Col xs={4} sm={6} className="d-flex align-items-center">
            <SearchBar></SearchBar>
          </Col>
          <Col className="d-flex flex-row align-items-center justify-content-end pr-2">
            <NotificationCenter></NotificationCenter>
            <Button
              href="https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=XHHRWXT9YB7WE&source=url"
              target="_blank"
            >
              <FontAwesomeIcon icon={faHeart}></FontAwesomeIcon>
            </Button>
            {offline ? (
              <ActionButton
                loading
                alwaysShowText
                className="ml-2"
                variant="warning"
                icon={faNetworkWired}
              >
                {isMobile ? "" : "Connecting..."}
              </ActionButton>
            ) : (
              serverActions
            )}
          </Col>
        </Row>
      </Container>
    </Navbar>
  );
};

export default Header;
