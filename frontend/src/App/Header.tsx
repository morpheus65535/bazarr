import {
  faBars,
  faHeart,
  faNetworkWired,
  faUser,
} from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import React, {
  FunctionComponent,
  useCallback,
  useContext,
  useMemo,
  useState,
} from "react";
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
import { useMovies, useSeries, useSystemSettings } from "../@redux/hooks";
import { useReduxAction } from "../@redux/hooks/base";
import { useIsOffline } from "../@redux/hooks/site";
import logo from "../@static/logo64.png";
import { SystemApi } from "../apis";
import { ActionIcon, SearchBar, SearchResult } from "../components";
import { useBaseUrl } from "../utilites";
import "./header.scss";

interface Props {}

const Header: FunctionComponent<Props> = () => {
  const setNeedAuth = useReduxAction(siteRedirectToAuth);

  const [series, updateSeries] = useSeries();
  const [movies, updateMovies] = useMovies();

  const [settings] = useSystemSettings();

  const canLogout = (settings.items?.auth.type ?? "none") !== "none";

  const toggleSidebar = useContext(SidebarToggleContext);

  const updateItems = useCallback(() => {
    if (series.items.length === 0) {
      updateSeries();
    }

    if (movies.items.length === 0) {
      updateMovies();
    }
  }, [series.items.length, movies.items.length, updateSeries, updateMovies]);

  const searchSeries = useCallback(
    (text: string): SearchResult[] => {
      text = text.toLowerCase();

      return series.items
        .filter((val) => val.title.toLowerCase().includes(text))
        .map((val) => {
          return {
            name: `${val.title} (${val.year})`,
            link: `/series/${val.sonarrSeriesId}`,
          };
        });
    },
    [series]
  );

  const searchMovies = useCallback(
    (text: string): SearchResult[] => {
      text = text.toLowerCase();

      return movies.items
        .filter((val) => val.title.toLowerCase().includes(text))
        .map((val) => {
          return {
            name: `${val.title} (${val.year})`,
            link: `/movies/${val.radarrId}`,
          };
        });
    },
    [movies]
  );

  const search = useCallback(
    (text: string): SearchResult[] => {
      const movies = searchMovies(text);
      const series = searchSeries(text);

      return [...movies, ...series];
    },
    [searchMovies, searchSeries]
  );

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

  const [reconnecting, setReconnect] = useState(false);
  const reconnect = useCallback(() => {
    setReconnect(true);
    SystemApi.status().finally(() => setReconnect(false));
  }, []);

  const baseUrl = useBaseUrl();

  return (
    <Navbar bg="primary" className="flex-grow-1 px-0">
      <div className="header-icon px-3 m-0 d-none d-md-block">
        <Navbar.Brand href={baseUrl} className="">
          <Image alt="brand" src={logo} width="32" height="32"></Image>
        </Navbar.Brand>
      </div>
      <Button className="mx-2 m-0 d-md-none" onClick={toggleSidebar}>
        <FontAwesomeIcon icon={faBars}></FontAwesomeIcon>
      </Button>
      <Container fluid>
        <Row noGutters className="flex-grow-1">
          <Col xs={6} sm={4} className="d-flex align-items-center">
            <SearchBar onFocus={updateItems} onSearch={search}></SearchBar>
          </Col>
          <Col className="d-flex flex-row align-items-center justify-content-end pr-2">
            <Button
              href="https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=XHHRWXT9YB7WE&source=url"
              target="_blank"
            >
              <FontAwesomeIcon icon={faHeart}></FontAwesomeIcon>
            </Button>
            {offline ? (
              <ActionIcon
                loading={reconnecting}
                className="ml-2"
                variant="warning"
                icon={faNetworkWired}
                onClick={reconnect}
              >
                Reconnect
              </ActionIcon>
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
