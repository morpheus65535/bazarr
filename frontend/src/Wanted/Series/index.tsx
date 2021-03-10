import { faSearch } from "@fortawesome/free-solid-svg-icons";
import React, { FunctionComponent } from "react";
import { Container, Row } from "react-bootstrap";
import { Helmet } from "react-helmet";
import { useWantedSeries } from "../../@redux/hooks";
import { SeriesApi } from "../../apis";
import { AsyncStateOverlay, ContentHeader } from "../../components";
import { useAutoUpdate } from "../../utilites/hooks";
import Table from "./table";

interface Props {}

const WantedSeriesView: FunctionComponent<Props> = () => {
  const [wanted, update] = useWantedSeries();
  useAutoUpdate(update);
  return (
    <AsyncStateOverlay state={wanted}>
      {(data) => (
        <Container fluid>
          <Helmet>
            <title>Wanted Series - Bazarr</title>
          </Helmet>
          <ContentHeader>
            <ContentHeader.AsyncButton
              disabled={data.length === 0}
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
