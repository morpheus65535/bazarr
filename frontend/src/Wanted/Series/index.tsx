import { faSearch } from "@fortawesome/free-solid-svg-icons";
import React, { FunctionComponent } from "react";
import { Container, Row } from "react-bootstrap";
import { Helmet } from "react-helmet";
import { useItemUpdater, useWantedSeries } from "../../@redux/hooks";
import { SeriesApi } from "../../apis";
import { AsyncStateOverlay, ContentHeader } from "../../components";
import Table from "./table";

interface Props {}

const WantedSeriesView: FunctionComponent<Props> = () => {
  const [wanted, update] = useWantedSeries();
  useItemUpdater(update);
  return (
    <AsyncStateOverlay state={wanted}>
      {(data) => (
        <Container fluid>
          <Helmet>
            <title>Wanted Series - Bazarr</title>
          </Helmet>
          <ContentHeader>
            <ContentHeader.AsyncButton
              promise={() => SeriesApi.action({ action: "search-wanted" })}
              onSuccess={update}
              icon={faSearch}
            >
              Search All
            </ContentHeader.AsyncButton>
          </ContentHeader>
          <Row>
            <Table wanted={data} update={update}></Table>
          </Row>
        </Container>
      )}
    </AsyncStateOverlay>
  );
};

export default WantedSeriesView;
