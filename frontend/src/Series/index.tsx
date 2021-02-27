import { faList } from "@fortawesome/free-solid-svg-icons";
import React, { FunctionComponent } from "react";
import { Container, Row } from "react-bootstrap";
import { Helmet } from "react-helmet";
import { connect } from "react-redux";
import { AsyncStateOverlay, ContentHeader } from "../components";
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
  return (
    <AsyncStateOverlay state={series}>
      {(data) => (
        <Container fluid>
          <Helmet>
            <title>Series - Bazarr</title>
          </Helmet>
          <ContentHeader>
            <ContentHeader.Button icon={faList}>Mass Edit</ContentHeader.Button>
          </ContentHeader>
          <Row>
            <Table series={data}></Table>
          </Row>
        </Container>
      )}
    </AsyncStateOverlay>
  );
};

export default connect(mapStateToProps)(SeriesView);
