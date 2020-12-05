import React from "react";
import { Container, Row } from "react-bootstrap";
import { connect } from "react-redux";
import { Helmet } from "react-helmet";

import { faList } from "@fortawesome/free-solid-svg-icons";

import {
  ContentHeader,
  ContentHeaderButton,
  EditItemModal,
} from "../components";

import Table from "./table";

interface Props {}
interface State {
  modal?: Movie;
}
class MovieView extends React.Component<Props, State> {
  constructor(props: Props) {
    super(props);

    this.state = {
      modal: undefined,
    };
  }

  onMovieEditClick(movie: Movie) {
    this.setState({
      ...this.state,
      modal: movie,
    });
  }

  onMovieEditClose() {
    this.setState({
      ...this.state,
      modal: undefined,
    });
  }
  render() {
    const { modal } = this.state;

    return (
      <Container fluid>
        <Helmet>
          <title>Movies - Bazarr</title>
        </Helmet>
        <Row className="flex-column">
          <ContentHeader>
            <ContentHeaderButton iconProps={{ icon: faList }}>
              Mass Edit
            </ContentHeaderButton>
          </ContentHeader>
          <Row className="p-3">
            <Table openMovieEditor={this.onMovieEditClick.bind(this)}></Table>
          </Row>
          <EditItemModal
            item={modal}
            onClose={this.onMovieEditClose.bind(this)}
          ></EditItemModal>
        </Row>
      </Container>
    );
  }
}

export default connect()(MovieView);
