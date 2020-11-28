import React from "react";
import { connect } from "react-redux";
import { Container } from "react-bootstrap";
import { CommonHeader, CommonHeaderBtn } from "../components/CommonHeader";

import { faList } from "@fortawesome/free-solid-svg-icons";

import Table from "./table";
import SeriesEditModal from "./Components/SeriesEditModal";

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
        <CommonHeader>
          <CommonHeaderBtn iconProps={{ icon: faList }}>
            Mass Edit
          </CommonHeaderBtn>
        </CommonHeader>
        <div className="p-3">
          <Table openSeriesEditor={this.onSeriesEditClick.bind(this)}></Table>
        </div>
        <SeriesEditModal
          series={modal}
          close={this.onSeriesEditorClose.bind(this)}
        ></SeriesEditModal>
      </Container>
    );
  }
}

export default connect(mapStateToProps)(SeriesView);
