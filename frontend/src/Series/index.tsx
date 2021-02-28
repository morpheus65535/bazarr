import React, { FunctionComponent, useState } from "react";
import { Container, Row } from "react-bootstrap";
import { Helmet } from "react-helmet";
import { connect } from "react-redux";
import { AsyncStateOverlay, ContentHeader } from "../components";
import EditModeHeader from "../components/EditModeHeader";
import Table from "./table";

interface Props {
  series: AsyncState<Series[]>;
}

function mapStateToProps({ series }: StoreState) {
  const { seriesList } = series;
  return {
    series: seriesList,
  };
}

const SeriesView: FunctionComponent<Props> = ({ series }) => {
  const editMode = useState(false);

  return (
    <AsyncStateOverlay state={series}>
      {(data) => (
        <Container fluid>
          <Helmet>
            <title>Series - Bazarr</title>
          </Helmet>
          <ContentHeader>
            <EditModeHeader editState={editMode}></EditModeHeader>
          </ContentHeader>
          <Row>
            <Table editMode={editMode[0]} series={data}></Table>
          </Row>
        </Container>
      )}
    </AsyncStateOverlay>
  );
};

export default connect(mapStateToProps)(SeriesView);
