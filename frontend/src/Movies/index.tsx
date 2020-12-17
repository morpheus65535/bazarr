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
class MovieView extends React.Component<Props> {
  render() {
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
          <Table></Table>
        </Row>
      </Container>
    );
  }
}

export default connect()(MovieView);
