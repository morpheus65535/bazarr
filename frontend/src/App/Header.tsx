import {
  faBars,
  faHeart,
  faNetworkWired,
  faUser,
} from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import React, { FunctionComponent, useContext, useMemo } from "react";
import {
  Button,
  Col,
  Container,
  Dropdown,
  Image,
  Navbar,
  Row,
} from "react-bootstrap";
import { SidebarToggleContext } from ".";
import { siteRedirectToAuth } from "../@redux/actions";
import { useSystemSettings } from "../@redux/hooks";
import { useReduxAction } from "../@redux/hooks/base";
import { useIsOffline } from "../@redux/hooks/site";
import logo from "../@static/logo64.png";
import { SystemApi } from "../apis";
import { ActionButton, SearchBar, SearchResult } from "../components";
import { useGotoHomepage } from "../utilites";
import "./header.scss";

async function SearchItem(text: string) {
  const results = await SystemApi.search(text);

  return results.map<SearchResult>((v) => {
    let link: string;
    if (v.sonarrSeriesId) {
      link = `/series/${v.sonarrSeriesId}`;
    } else if (v.radarrId) {
      link = `/movies/${v.radarrId}`;
    } else {
      link = "";
    }
    return {
      name: `${v.title} (${v.year})`,
      link,
    };
  });
}

interface Props {}

const Header: FunctionComponent<Props> = () => {
  const setNeedAuth = useReduxAction(siteRedirectToAuth);

  const [settings] = useSystemSettings();

  const canLogout = (settings.content?.auth.type ?? "none") === "form";

  const toggleSidebar = useContext(SidebarToggleContext);

  const offline = useIsOffline();

  const dropdown = useMemo(
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
      <Button className="mx-2 m-0 d-md-none" onClick={toggleSidebar}>
        <FontAwesomeIcon icon={faBars}></FontAwesomeIcon>
      </Button>
      <Container fluid>
        <Row noGutters className="flex-grow-1">
          <Col xs={6} sm={4} className="d-flex align-items-center">
            <SearchBar onSearch={SearchItem}></SearchBar>
          </Col>
          <Col className="d-flex flex-row align-items-center justify-content-end pr-2">
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
                Connecting...
              </ActionButton>
            ) : (
              dropdown
            )}
          </Col>
        </Row>
      </Container>
    </Navbar>
  );
};

export default Header;
