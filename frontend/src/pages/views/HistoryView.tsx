import { UsePaginationQueryResult } from "@/apis/queries/hooks";
import { Container } from "@mantine/core";
import { useDocumentTitle } from "@mantine/hooks";
import { Column } from "react-table";
import { QueryPageTable } from "../../components";

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
  useDocumentTitle(`${name} History - Bazarr`);
  return (
    <Container fluid px={0}>
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
