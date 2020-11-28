import React from "react";
import { connect } from "react-redux";
import { Container } from "react-bootstrap";
import { CommonHeader, CommonHeaderBtn } from "../components/CommonHeader";

import { faList } from "@fortawesome/free-solid-svg-icons";

import Table from "./table";
import SeriesEditModal from "./Components/SeriesEditModal";

interface Props {
  modal?: Series;
}

function mapStateToProps({ series }: StoreState) {
  const { seriesModal } = series;
  return {
    modal: seriesModal,
  };
}

class SeriesView extends React.Component<Props> {
  constructor(props: Props) {
    super(props);
  }

  onSeriesEditClick(serie: Series) {}

  render(): JSX.Element {
    const { modal } = this.props;
    return (
      <Container fluid className="px-0">
        <CommonHeader>
          <CommonHeaderBtn iconProps={{ icon: faList }}>
            Mass Edit
          </CommonHeaderBtn>
        </CommonHeader>
        <div className="p-3">
          <Table></Table>
        </div>
        <SeriesEditModal></SeriesEditModal>
      </Container>
    );
  }
}

export default connect(mapStateToProps)(SeriesView);
