import React from "react";
import { Container, Row } from "react-bootstrap";
import { Helmet } from "react-helmet";

import { connect } from "react-redux";
import { updateWantedSeriesList } from "../../@redux/actions";

import { faSearch } from "@fortawesome/free-solid-svg-icons";

import { ContentHeader, ContentHeaderButton } from "../../components";

import Table from "./table";

interface Props {
  update: () => void;
}

class WantedSeriesView extends React.Component<Props> {
  componentDidMount() {
    this.props.update();
  }
  render(): JSX.Element {
    return (
      <Container fluid>
        <Helmet>
          <title>Wanted Series - Bazarr</title>
        </Helmet>
        <Row className="flex-column">
          <ContentHeader>
            <ContentHeaderButton iconProps={{ icon: faSearch }}>
              Search All
            </ContentHeaderButton>
          </ContentHeader>
          <div className="p-3">
            <Table></Table>
          </div>
        </Row>
      </Container>
    );
  }
}

export default connect(null, {
  update: updateWantedSeriesList,
})(WantedSeriesView);
