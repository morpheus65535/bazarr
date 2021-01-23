import React from "react";
import { connect } from "react-redux";
import { Container, Row } from "react-bootstrap";
import { faList } from "@fortawesome/free-solid-svg-icons";
import { Helmet } from "react-helmet";

import { ContentHeader, ContentHeaderButton } from "../components";
import Table from "./table";

interface Props {}

function mapStateToProps({ series }: StoreState) {
  return {};
}

class SeriesView extends React.Component<Props> {
  render(): JSX.Element {
    return (
      <Container fluid>
        <Helmet>
          <title>Series - Bazarr</title>
        </Helmet>
        <ContentHeader>
          <ContentHeaderButton icon={faList}>Mass Edit</ContentHeaderButton>
        </ContentHeader>
        <Row>
          <Table></Table>
        </Row>
      </Container>
    );
  }
}

export default connect(mapStateToProps)(SeriesView);
