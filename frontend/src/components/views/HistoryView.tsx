import React from "react";
import { Container, Row } from "react-bootstrap";
import { Helmet } from "react-helmet";
import { Column } from "react-table";
import { PaginationQuery } from "src/apis/queries/hooks";
import { QueryPageTable } from "..";

interface Props<T extends History.Base> {
  name: string;
  query: PaginationQuery<T>;
  columns: Column<T>[];
}

function HistoryView<T extends History.Base = History.Base>({
  columns,
  name,
  query,
}: Props<T>) {
  return (
    <Container fluid>
      <Helmet>
        <title>{name} History - Bazarr</title>
      </Helmet>
      <Row>
        <QueryPageTable
          emptyText={`Nothing Found in ${name} History`}
          columns={columns}
          query={query}
          data={[]}
        ></QueryPageTable>
      </Row>
    </Container>
  );
}

export default HistoryView;
