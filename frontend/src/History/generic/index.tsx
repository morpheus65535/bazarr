import { capitalize } from "lodash";
import React, { FunctionComponent } from "react";
import { Container, Row } from "react-bootstrap";
import { Helmet } from "react-helmet";
import { Column } from "react-table";
import { AsyncStateOverlay, PageTable } from "../../components";

interface Props {
  type: "movies" | "series";
  state: Readonly<AsyncState<History.Base[]>>;
  columns: Column<History.Base>[];
}

const HistoryGenericView: FunctionComponent<Props> = ({
  state,
  columns,
  type,
}) => {
  const typeName = capitalize(type);
  return (
    <Container fluid>
      <Helmet>
        <title>{typeName} History - Bazarr</title>
      </Helmet>
      <Row>
        <AsyncStateOverlay state={state}>
          {({ data }) => (
            <PageTable
              emptyText={`Nothing Found in ${typeName} History`}
              columns={columns}
              data={data}
            ></PageTable>
          )}
        </AsyncStateOverlay>
      </Row>
    </Container>
  );
};

export default HistoryGenericView;
