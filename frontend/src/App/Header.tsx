import React, { FunctionComponent, useCallback, useContext } from "react";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faUser, faHeart, faBars } from "@fortawesome/free-solid-svg-icons";
import {
  Image,
  Dropdown,
  Navbar,
  Container,
  Row,
  Col,
  Button,
} from "react-bootstrap";

import { SystemApi } from "../apis";

import { connect } from "react-redux";

import { SearchResult, SearchBar } from "../components";

import { SidebarToggleContext } from ".";

import logo from "../@static/logo64.png";

interface Props {
  movies: Movie[];
  series: Series[];
}

function mapStateToProps({ series, movie }: StoreState) {
  return {
    movies: movie.movieList.items,
    series: series.seriesList.items,
  };
}

const Header: FunctionComponent<Props> = (props) => {
  const { series, movies } = props;

  const toggleSidebar = useContext(SidebarToggleContext);

  const searchSeries = useCallback(
    (text: string): SearchResult[] => {
      text = text.toLowerCase();

      return series
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

      return movies
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

  const baseUrl =
    process.env.NODE_ENV === "production" ? window.Bazarr.baseUrl : "/";

  return (
    <Navbar bg="light" className="flex-grow-1 px-0">
      <div className="header-icon px-3 m-0 d-none d-md-block">
        <Navbar.Brand href={baseUrl} className="">
          <Image alt="brand" src={logo} width="32" height="32"></Image>
        </Navbar.Brand>
      </div>
      <Button
        variant="light"
        className="mx-2 m-0 d-md-none"
        onClick={toggleSidebar}
      >
        <FontAwesomeIcon icon={faBars}></FontAwesomeIcon>
      </Button>
      <Container fluid>
        <Row noGutters className="flex-grow-1">
          <Col xs={6} sm={4} className="d-flex align-items-center">
            <SearchBar onSearch={search}></SearchBar>
          </Col>
          <Col className="d-flex flex-row align-items-center justify-content-end pr-2">
            <Button
              variant="light"
              href="https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=XHHRWXT9YB7WE&source=url"
              target="_blank"
            >
              <FontAwesomeIcon icon={faHeart}></FontAwesomeIcon>
            </Button>
            <Dropdown alignRight>
              <Dropdown.Toggle
                className="dropdown-hidden"
                as={Button}
                variant="light"
              >
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
              </Dropdown.Menu>
            </Dropdown>
          </Col>
        </Row>
      </Container>
    </Navbar>
  );
};

export default connect(mapStateToProps)(Header);
