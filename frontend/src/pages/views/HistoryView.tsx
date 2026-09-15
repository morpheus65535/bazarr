import { Container } from "@mantine/core";
import { useDocumentTitle } from "@mantine/hooks";
import { useInstanceName } from "@/apis/hooks/site";
import { UsePaginationQueryResult } from "@/apis/queries/hooks";
import { QueryPageTable } from "@/components";
import { AppColumnDef as ColumnDef } from "@/components/tables/features";

interface Props<T extends History.Base> {
  name: string;
  query: UsePaginationQueryResult<T>;
  columns: ColumnDef<T>[];
}

const HistoryView = <T extends History.Base = History.Base>({
  columns,
  name,
  query,
}: Props<T>) => {
  useDocumentTitle(`${name} History - ${useInstanceName()}`);
  return (
    <Container fluid px={0}>
      <QueryPageTable
        tableStyles={{ emptyText: `Nothing Found in ${name} History` }}
        columns={columns}
        query={query}
      ></QueryPageTable>
    </Container>
  );
};

export default HistoryView;
