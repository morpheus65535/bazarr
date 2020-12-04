import React from "react";
import { connect } from "react-redux";
import { Container } from "react-bootstrap";
import { faList } from "@fortawesome/free-solid-svg-icons";
import { Helmet } from "react-helmet";

import {
  ContentHeader,
  ContentHeaderButton,
  EditItemModal,
} from "../components";
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
      <Container fluid className="px-0">
        <Helmet>
          <title>Series - Bazarr</title>
        </Helmet>
        <ContentHeader>
          <ContentHeaderButton iconProps={{ icon: faList }}>
            Mass Edit
          </ContentHeaderButton>
        </ContentHeader>
        <div className="p-3">
          <Table openSeriesEditor={this.onSeriesEditClick.bind(this)}></Table>
        </div>
        <EditItemModal
          item={modal}
          onClose={this.onSeriesEditorClose.bind(this)}
        ></EditItemModal>
      </Container>
    );
  }
}

export default connect(mapStateToProps)(SeriesView);
