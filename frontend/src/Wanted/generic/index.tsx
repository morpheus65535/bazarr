import { faSearch } from "@fortawesome/free-solid-svg-icons";
import { capitalize } from "lodash";
import React from "react";
import { Container, Row } from "react-bootstrap";
import { Helmet } from "react-helmet";
import { Column } from "react-table";
import { AsyncPageTable, ContentHeader } from "../../components";

interface Props<T extends Wanted.Base> {
  type: "movies" | "series";
  columns: Column<T>[];
  state: Readonly<AsyncOrderState<T>>;
  loader: (params: Parameter.Range) => void;
  searchAll: () => Promise<void>;
}

function GenericWantedView<T extends Wanted.Base>({
  type,
  columns,
  state,
  loader,
  searchAll,
}: Props<T>) {
  const typeName = capitalize(type);

  const dataCount = Object.keys(state.data.items).length;

  return (
    <Container fluid>
      <Helmet>
        <title>Wanted {typeName} - Bazarr</title>
      </Helmet>
      <ContentHeader>
        <ContentHeader.AsyncButton
          disabled={dataCount === 0}
          promise={searchAll}
          icon={faSearch}
        >
          Search All
        </ContentHeader.AsyncButton>
      </ContentHeader>
      <Row>
        <AsyncPageTable
          aos={state}
          loader={loader}
          emptyText={`No Missing ${typeName} Subtitles`}
          columns={columns}
          data={[]}
        ></AsyncPageTable>
      </Row>
    </Container>
  );
}

export default GenericWantedView;
