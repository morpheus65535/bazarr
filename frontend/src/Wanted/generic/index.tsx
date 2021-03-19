import { faSearch } from "@fortawesome/free-solid-svg-icons";
import { capitalize } from "lodash";
import React, { FunctionComponent } from "react";
import { Container, Row } from "react-bootstrap";
import { Helmet } from "react-helmet";
import { Column } from "react-table";
import { AsyncStateOverlay, ContentHeader, PageTable } from "../../components";

interface Props {
  type: "movies" | "series";
  columns: Column<Wanted.Base>[];
  state: Readonly<AsyncState<Wanted.Base[]>>;
  update: () => void;
  searchAll: () => Promise<void>;
}

const GenericWantedView: FunctionComponent<Props> = ({
  type,
  columns,
  state,
  update,
  searchAll,
}) => {
  const typeName = capitalize(type);
  return (
    <AsyncStateOverlay state={state}>
      {(data) => (
        <Container fluid>
          <Helmet>
            <title>Wanted {typeName} - Bazarr</title>
          </Helmet>
          <ContentHeader>
            <ContentHeader.AsyncButton
              disabled={data.length === 0}
              promise={searchAll}
              onSuccess={update}
              icon={faSearch}
            >
              Search All
            </ContentHeader.AsyncButton>
          </ContentHeader>
          <Row>
            <PageTable
              emptyText={`No Missing ${typeName} Subtitles`}
              columns={columns}
              data={data}
            ></PageTable>
          </Row>
        </Container>
      )}
    </AsyncStateOverlay>
  );
};

export default GenericWantedView;
