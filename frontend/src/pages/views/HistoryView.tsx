import { Container } from "@mantine/core";
import { useDocumentTitle } from "@mantine/hooks";
import { ColumnDef } from "@tanstack/react-table";
import { UsePaginationQueryResult } from "@/apis/queries/hooks";
import { QueryPageTable } from "@/components";

interface Props<T extends History.Base> {
  name: string;
  query: UsePaginationQueryResult<T>;
  columns: ColumnDef<T>[];
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
        tableStyles={{ emptyText: `Nothing Found in ${name} History` }}
        columns={columns}
        query={query}
      ></QueryPageTable>
    </Container>
  );
}

export default HistoryView;
