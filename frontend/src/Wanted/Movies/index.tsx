import React from "react";
import { Container } from "react-bootstrap";

import { connect } from "react-redux";
import { updateWantedMovieList } from "../../redux/actions/movie";

import { faSearch } from "@fortawesome/free-solid-svg-icons";

import Table from "./table";

import ContentHeader, {
  ContentHeaderButton,
} from "../../components/ContentHeader";

interface Props {
  update: () => void;
}

class WantedMoviesView extends React.Component<Props> {
  componentDidMount() {
    this.props.update();
  }
  render() {
    return (
      <Container fluid className="p-0">
        <ContentHeader>
          <ContentHeaderButton iconProps={{ icon: faSearch }}>
            Search All
          </ContentHeaderButton>
        </ContentHeader>
        <div className="p-3">
          <Table></Table>
        </div>
      </Container>
    );
  }
}

export default connect(null, { update: updateWantedMovieList })(
  WantedMoviesView
);
