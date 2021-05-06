import { faSearch } from "@fortawesome/free-solid-svg-icons";
import { capitalize } from "lodash";
import React, { useMemo } from "react";
import { Container, Row } from "react-bootstrap";
import { Helmet } from "react-helmet";
import { Column } from "react-table";
import { ContentHeader, PageTable } from "../../components";
import { buildOrderList, GetItemId } from "../../utilites";

interface Props<T extends Wanted.Base> {
  type: "movies" | "series";
  columns: Column<T>[];
  state: Readonly<AsyncOrderState<T>>;
  loader: (start: number, length: number) => void;
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

  const data = useMemo(() => buildOrderList(state.data), [state.data]);

  return (
    <Container fluid>
      <Helmet>
        <title>Wanted {typeName} - Bazarr</title>
      </Helmet>
      <ContentHeader>
        <ContentHeader.AsyncButton
          disabled={data.length === 0}
          promise={searchAll}
          icon={faSearch}
        >
          Search All
        </ContentHeader.AsyncButton>
      </ContentHeader>
      <Row>
        <PageTable
          async
          asyncState={state}
          asyncId={GetItemId}
          asyncLoader={loader}
          emptyText={`No Missing ${typeName} Subtitles`}
          columns={columns}
          data={data}
        ></PageTable>
      </Row>
    </Container>
  );
}

export default GenericWantedView;
