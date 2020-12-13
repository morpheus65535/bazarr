import React from "react";
import { Container, Row } from "react-bootstrap";
import { connect } from "react-redux";
import { Helmet } from "react-helmet";

import { faList } from "@fortawesome/free-solid-svg-icons";

import {
  ContentHeader,
  ContentHeaderButton,
  ItemEditorModal,
} from "../Components";

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
        <Row>
          <ContentHeader>
            <ContentHeaderButton iconProps={{ icon: faList }}>
              Mass Edit
            </ContentHeaderButton>
          </ContentHeader>
        </Row>
        <Row>
          <Table openMovieEditor={this.onMovieEditClick.bind(this)}></Table>
        </Row>
        <ItemEditorModal
          show={modal !== undefined}
          title={modal?.title}
          onClose={this.onMovieEditClose.bind(this)}
        ></ItemEditorModal>
      </Container>
    );
  }
}

export default connect()(MovieView);
