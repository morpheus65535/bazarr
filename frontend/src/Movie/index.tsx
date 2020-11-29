import React from "react";
import { connect } from "react-redux";

import { faList } from "@fortawesome/free-solid-svg-icons";

import ContentHeader, {
  ContentHeaderButton,
} from "../components/ContentHeader";
import { Container } from "react-bootstrap";

import Table from "./table";
class MovieView extends React.Component {
  render() {
    return (
      <Container fluid className="p-0">
        <ContentHeader>
          <ContentHeaderButton iconProps={{ icon: faList }}>
            Mass Edit
          </ContentHeaderButton>
        </ContentHeader>
        <div className="p-3">
          <Table></Table>
        </div>
      </Container>
    );
  }
}

export default connect()(MovieView);
