import React, { FunctionComponent, ChangeEvent } from "react";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faUser, faHeart } from "@fortawesome/free-solid-svg-icons";
import { Dropdown, Form, Nav, Navbar, NavLink, NavItem } from "react-bootstrap";
import { throttle } from "lodash";

import { connect } from "react-redux";
import { useHistory } from "react-router";

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
    // TODO: UpdateSearchResult
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

    return (
      <Navbar bg="light" className="header">
        <Nav className="mr-auto">
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
        </Nav>
        <Nav>
          <Nav.Link>
            <FontAwesomeIcon icon={faHeart}></FontAwesomeIcon>
          </Nav.Link>
          <Dropdown alignRight as={NavItem}>
            <Dropdown.Toggle as={NavLink}>
              <FontAwesomeIcon icon={faUser}></FontAwesomeIcon>
            </Dropdown.Toggle>
            <Dropdown.Menu>
              <Dropdown.Item>Restart</Dropdown.Item>
              <Dropdown.Item>Shutdown</Dropdown.Item>
            </Dropdown.Menu>
          </Dropdown>
        </Nav>
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
