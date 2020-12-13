import React from "react";
import { connect } from "react-redux";
import { Container, Row } from "react-bootstrap";
import { faList } from "@fortawesome/free-solid-svg-icons";
import { Helmet } from "react-helmet";

import {
  ContentHeader,
  ContentHeaderButton,
  ItemEditorModal,
} from "../Components";
import Table from "./table";

interface Props {}

interface State {
  modal?: Series;
}

function mapStateToProps({ series }: StoreState) {
  return {};
}

class SeriesView extends React.Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = {
      modal: undefined,
    };
  }

  onSeriesEditClick(series: Series) {
    this.setState({
      ...this.state,
      modal: series,
    });
  }

  onSeriesEditorClose() {
    this.setState({
      ...this.state,
      modal: undefined,
    });
  }

  render(): JSX.Element {
    const { modal } = this.state;

    return (
      <Container fluid>
        <Helmet>
          <title>Series - Bazarr</title>
        </Helmet>
        <Row>
          <ContentHeader>
            <ContentHeaderButton iconProps={{ icon: faList }}>
              Mass Edit
            </ContentHeaderButton>
          </ContentHeader>
        </Row>
        <Row>
          <Table openSeriesEditor={this.onSeriesEditClick.bind(this)}></Table>
        </Row>
        <ItemEditorModal
          show={modal !== undefined}
          title={modal?.title}
          onClose={this.onSeriesEditorClose.bind(this)}
        ></ItemEditorModal>
      </Container>
    );
  }
}

export default connect(mapStateToProps)(SeriesView);
