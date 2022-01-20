import {
  faBars,
  faHeart,
  faNetworkWired,
  faUser,
} from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { uniqueId } from "lodash";
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
import {
  siteChangeSidebarVisibility,
  siteRedirectToAuth,
} from "../@redux/actions";
import { useReduxAction } from "../@redux/hooks/base";
import { useIsOffline } from "../@redux/hooks/site";
import logo from "../@static/logo64.png";
import { SystemApi, useSystemSettings } from "../apis";
import { ActionButton, SearchBar, SearchResult } from "../components";
import { useGotoHomepage, useIsMobile } from "../utilities";
import "./header.scss";
import NotificationCenter from "./Notification";

async function SearchItem(text: string) {
  const results = await SystemApi.search(text);

  return results.map<SearchResult>((v) => {
    let link: string;
    let id: string;
    if (v.sonarrSeriesId) {
      link = `/series/${v.sonarrSeriesId}`;
      id = `series-${v.sonarrSeriesId}`;
    } else if (v.radarrId) {
      link = `/movies/${v.radarrId}`;
      id = `movie-${v.radarrId}`;
    } else {
      link = "";
      id = uniqueId("unknown");
    }

    return {
      name: `${v.title} (${v.year})`,
      link,
      id,
    };
  });
}

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
              SystemApi.restart();
            }}
          >
            Restart
          </Dropdown.Item>
          <Dropdown.Item
            onClick={() => {
              SystemApi.shutdown();
            }}
          >
            Shutdown
          </Dropdown.Item>
          <Dropdown.Divider hidden={!canLogout}></Dropdown.Divider>
          <Dropdown.Item
            hidden={!canLogout}
            onClick={() => {
              SystemApi.logout().then(() => setNeedAuth());
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
            <SearchBar onSearch={SearchItem}></SearchBar>
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
