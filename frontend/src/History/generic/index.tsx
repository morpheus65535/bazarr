import { capitalize } from "lodash";
import React from "react";
import { Container, Row } from "react-bootstrap";
import { Helmet } from "react-helmet";
import { Column } from "react-table";
import { AsyncPageTable } from "../../components";

interface Props<T extends History.Base> {
  type: "movies" | "series";
  query: RangeQuery<T>;
  columns: Column<T>[];
}

function HistoryGenericView<T extends History.Base = History.Base>({
  columns,
  type,
  query,
}: Props<T>) {
  const typeName = capitalize(type);
  return (
    <Container fluid>
      <Helmet>
        <title>{typeName} History - Bazarr</title>
      </Helmet>
      <Row>
        <AsyncPageTable
          emptyText={`Nothing Found in ${typeName} History`}
          columns={columns}
          keys={[type]}
          query={query}
          data={[]}
        ></AsyncPageTable>
      </Row>
    </Container>
  );
}

export default HistoryGenericView;
