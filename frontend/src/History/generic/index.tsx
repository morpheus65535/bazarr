import { capitalize } from "lodash";
import React from "react";
import { Container, Row } from "react-bootstrap";
import { Helmet } from "react-helmet";
import { Column } from "react-table";
import { AsyncPageTable } from "../../components";

interface Props<T extends History.Base> {
  type: "movies" | "series";
  state: Readonly<Async.Entity<T>>;
  loader: (param: Parameter.Range) => void;
  columns: Column<T>[];
}

function HistoryGenericView<T extends History.Base = History.Base>({
  state,
  loader,
  columns,
  type,
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
          entity={state}
          loader={loader}
          columns={columns}
          data={[]}
        ></AsyncPageTable>
      </Row>
    </Container>
  );
}

export default HistoryGenericView;
