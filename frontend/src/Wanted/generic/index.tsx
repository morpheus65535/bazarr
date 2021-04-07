import { faSearch } from "@fortawesome/free-solid-svg-icons";
import { capitalize } from "lodash";
import React, { FunctionComponent, useMemo } from "react";
import { Container, Row } from "react-bootstrap";
import { Helmet } from "react-helmet";
import { Column } from "react-table";
import { ContentHeader, PageTable } from "../../components";
import { buildOrderList, GetItemId } from "../../utilites";

interface Props {
  type: "movies" | "series";
  columns: Column<Wanted.Base>[];
  state: Readonly<AsyncState<OrderIdState<Wanted.Base>>>;
  loader: (start: number, length: number) => void;
  searchAll: () => Promise<void>;
}

const GenericWantedView: FunctionComponent<Props> = ({
  type,
  columns,
  state,
  loader,
  searchAll,
}) => {
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
};

export default GenericWantedView;
