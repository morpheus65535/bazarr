import { faSearch } from "@fortawesome/free-solid-svg-icons";
import { capitalize } from "lodash";
import React, { FunctionComponent, useCallback, useMemo } from "react";
import { Container, Row } from "react-bootstrap";
import { Helmet } from "react-helmet";
import { Column, TableUpdater } from "react-table";
import { ContentHeader, PageTable } from "../../components";
import { buildOrderList, GetItemId } from "../../utilites";

interface Props {
  type: "movies" | "series";
  columns: Column<Wanted.Base>[];
  state: Readonly<AsyncState<OrderIdState<Wanted.Base>>>;
  loader: (start: number, length: number) => void;
  update: (id?: number) => void;
  searchAll: () => Promise<void>;
}

const GenericWantedView: FunctionComponent<Props> = ({
  type,
  columns,
  state,
  update,
  loader,
  searchAll,
}) => {
  const typeName = capitalize(type);

  const data = useMemo(() => buildOrderList(state.data), [state.data]);

  const updater = useCallback<TableUpdater<Wanted.Base>>(
    (row, id: number) => {
      update(id);
    },
    [update]
  );

  return (
    <Container fluid>
      <Helmet>
        <title>Wanted {typeName} - Bazarr</title>
      </Helmet>
      <ContentHeader>
        <ContentHeader.AsyncButton
          disabled={data.length === 0}
          promise={searchAll}
          onSuccess={update as () => void}
          icon={faSearch}
        >
          Search All
        </ContentHeader.AsyncButton>
      </ContentHeader>
      <Row>
        <PageTable
          async
          idState={state}
          idGetter={GetItemId}
          loader={loader}
          emptyText={`No Missing ${typeName} Subtitles`}
          columns={columns}
          update={updater}
          data={data}
        ></PageTable>
      </Row>
    </Container>
  );
};

export default GenericWantedView;
