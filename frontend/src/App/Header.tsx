import React from "react";
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

import { connect } from "react-redux";

import { SearchResult, SearchBar } from "../Components";

import logo from "../@static/logo128.png";

interface Props {
  movies: Movie[];
  series: Series[];
  onToggle?: () => void;
}

function mapStateToProps({ series, movie }: StoreState) {
  return {
    movies: movie.movieList.items,
    series: series.seriesList.items,
  };
}

class Header extends React.Component<Props> {
  searchSeries(text: string): SearchResult[] {
    const { series } = this.props;

    text = text.toLowerCase();

    return series
      .filter((val) => val.title.toLowerCase().includes(text))
      .map((val) => {
        return {
          name: `${val.title} (${val.year})`,
          link: `/series/${val.sonarrSeriesId}`,
        };
      });
  }

  searchMovies(text: string): SearchResult[] {
    const { movies } = this.props;

    text = text.toLowerCase();

    return movies
      .filter((val) => val.title.toLowerCase().includes(text))
      .map((val) => {
        return {
          name: `${val.title} (${val.year})`,
          link: `/movies/${val.radarrId}`,
        };
      });
  }

  search(text: string): SearchResult[] {
    const movies = this.searchMovies(text);
    const series = this.searchSeries(text);

    return [...movies, ...series];
  }

  render() {
    const { onToggle } = this.props;

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
          onClick={onToggle}
        >
          <FontAwesomeIcon icon={faBars}></FontAwesomeIcon>
        </Button>
        <Container fluid>
          <Row noGutters className="flex-grow-1">
            <Col xs={6} sm={4} className="d-flex align-items-center">
              <SearchBar
                size="sm"
                onSearch={this.search.bind(this)}
              ></SearchBar>
            </Col>
            <Col className="d-flex flex-row align-items-center justify-content-end pr-2">
              <Button variant="light">
                <FontAwesomeIcon icon={faHeart}></FontAwesomeIcon>
              </Button>
              <Dropdown alignRight>
                <Dropdown.Toggle as={Button} variant="light">
                  <FontAwesomeIcon icon={faUser}></FontAwesomeIcon>
                </Dropdown.Toggle>
                <Dropdown.Menu>
                  <Dropdown.Item>Restart</Dropdown.Item>
                  <Dropdown.Item>Shutdown</Dropdown.Item>
                </Dropdown.Menu>
              </Dropdown>
            </Col>
          </Row>
        </Container>
      </Navbar>
    );
  }
}

export default connect(mapStateToProps)(Header);
