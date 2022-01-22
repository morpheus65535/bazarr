import React from "react";
import { Container, Row } from "react-bootstrap";
import { Helmet } from "react-helmet";
import { Column } from "react-table";
import { AsyncPageTable } from "../../components";

interface Props<T extends History.Base> {
  name: string;
  keys: string[];
  query: RangeQuery<T>;
  columns: Column<T>[];
}

function HistoryGenericView<T extends History.Base = History.Base>({
  columns,
  name,
  keys,
  query,
}: Props<T>) {
  return (
    <Container fluid>
      <Helmet>
        <title>{name} History - Bazarr</title>
      </Helmet>
      <Row>
        <AsyncPageTable
          emptyText={`Nothing Found in ${name} History`}
          columns={columns}
          keys={keys}
          query={query}
          data={[]}
        ></AsyncPageTable>
      </Row>
    </Container>
  );
}

export default HistoryGenericView;
