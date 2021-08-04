import { capitalize } from "lodash";
import React, { FunctionComponent } from "react";
import { Container, Row } from "react-bootstrap";
import { Helmet } from "react-helmet";
import { Column } from "react-table";
import { AsyncOverlay, PageTable } from "../../components";

interface Props {
  type: "movies" | "series";
  state: Readonly<Async.List<History.Base>>;
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
        <AsyncOverlay ctx={state}>
          {({ content }) => (
            <PageTable
              emptyText={`Nothing Found in ${typeName} History`}
              columns={columns}
              data={content}
            ></PageTable>
          )}
        </AsyncOverlay>
      </Row>
    </Container>
  );
};

export default HistoryGenericView;
