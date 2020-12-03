import React from "react";
import { Container } from "react-bootstrap";
import { connect } from "react-redux";
import { Helmet } from "react-helmet";

import { updateHistorySeriesList } from "../../@redux/actions/series";

import Table from "./table";

interface Props {
  update: () => void;
}

class SeriesHistoryView extends React.Component<Props> {
  componentDidMount() {
    this.props.update();
  }
  render() {
    return (
      <Container fluid className="m-1">
        <Helmet>
          <title>Series History - Bazarr</title>
        </Helmet>
        <Table></Table>
      </Container>
    );
  }
}

export default connect(null, { update: updateHistorySeriesList })(
  SeriesHistoryView
);
