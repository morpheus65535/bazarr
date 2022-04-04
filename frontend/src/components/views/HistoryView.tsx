import { UsePaginationQueryResult } from "@/apis/queries/hooks";
import { Container } from "@mantine/core";
import { Helmet } from "react-helmet";
import { Column } from "react-table";
import { QueryPageTable } from "..";

interface Props<T extends History.Base> {
  name: string;
  query: UsePaginationQueryResult<T>;
  columns: Column<T>[];
}

function HistoryView<T extends History.Base = History.Base>({
  columns,
  name,
  query,
}: Props<T>) {
  return (
    <Container fluid px={0}>
      <Helmet>
        <title>{name} History - Bazarr</title>
      </Helmet>
      <QueryPageTable
        emptyText={`Nothing Found in ${name} History`}
        columns={columns}
        query={query}
        data={[]}
      ></QueryPageTable>
    </Container>
  );
}

export default HistoryView;
