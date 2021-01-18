import React, { FunctionComponent, ChangeEvent } from "react";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faUser, faHeart, faBars } from "@fortawesome/free-solid-svg-icons";
import {
  Image,
  Dropdown,
  Form,
  Navbar,
  Container,
  Row,
  Col,
  Button,
} from "react-bootstrap";
import { throttle } from "lodash";

import { connect } from "react-redux";
import { useHistory } from "react-router";

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

interface SearchResult {
  name: string;
  link: string;
}

interface State {
  searchText: string;
  results: SearchResult[];
}

class Header extends React.Component<Props, State> {
  constructor(props: Props) {
    super(props);

    this.state = {
      searchText: "",
      results: [],
    };
  }

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

  updateSearchText = throttle((text: string) => {
    this.setState({
      ...this.state,
      searchText: text,
      results: this.search(text),
    });
  }, 500);

  onSearch(e: ChangeEvent<HTMLInputElement>) {
    const text = e.target.value;
    this.updateSearchText(text);
  }

  onClear() {
    this.setState({
      ...this.state,
      searchText: "",
      results: [],
    });
  }

  render() {
    const { searchText, results } = this.state;
    const { onToggle } = this.props;

    const items = results.map((val) => (
      <ResultItem
        {...val}
        key={val.name}
        clear={this.onClear.bind(this)}
      ></ResultItem>
    ));

    if (items.length === 0) {
      items.push(<Dropdown.Header key="notify">No Found</Dropdown.Header>);
    }

    const baseUrl =
      process.env.NODE_ENV === "production" ? window.Bazarr.baseUrl : "/";

    return (
      <Navbar bg="light" className="flex-grow-1 px-0">
        <Navbar.Brand
          href={baseUrl}
          className="header-icon px-3 m-0 d-none d-md-block"
        >
          <Image alt="brand" src={logo} width="32" height="32"></Image>
        </Navbar.Brand>
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
              <Dropdown show={searchText.length !== 0}>
                <Form.Control
                  type="text"
                  size="sm"
                  placeholder="Search..."
                  onChange={this.onSearch.bind(this)}
                ></Form.Control>
                <Dropdown.Menu style={{ maxHeight: 256, overflowY: "scroll" }}>
                  {items}
                </Dropdown.Menu>
              </Dropdown>
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

interface ResultItemProps extends SearchResult {
  clear?: () => void;
}

const ResultItem: FunctionComponent<ResultItemProps> = ({
  name,
  link,
  clear,
}) => {
  const history = useHistory();

  return (
    <Dropdown.Item
      onClick={(e) => {
        e.preventDefault();
        clear && clear();
        history.push(link);
      }}
    >
      <span>{name}</span>
    </Dropdown.Item>
  );
};

export default connect(mapStateToProps)(Header);
