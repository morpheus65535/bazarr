import { Container } from "@mantine/core";
import { useDocumentTitle } from "@mantine/hooks";
import { faSearch } from "@fortawesome/free-solid-svg-icons";
import { useIsAnyActionRunning } from "@/apis/hooks";
import { useInstanceName } from "@/apis/hooks/site";
import { UsePaginationQueryResult } from "@/apis/queries/hooks";
import { QueryPageTable, Toolbox } from "@/components";
import { AppColumnDef as ColumnDef } from "@/components/tables/features";

interface Props<T extends Wanted.Base> {
  name: string;
  columns: ColumnDef<T>[];
  query: UsePaginationQueryResult<T>;
  searchAll: () => Promise<void>;
}

function WantedView<T extends Wanted.Base>({
  name,
  columns,
  query,
  searchAll,
}: Props<T>) {
  const dataCount = query.paginationStatus.totalCount;
  const hasTask = useIsAnyActionRunning();

  useDocumentTitle(`Wanted ${name} - ${useInstanceName()}`);

  return (
    <Container fluid px={0}>
      <Toolbox>
        <Toolbox.Button
          disabled={hasTask || dataCount === 0}
          onClick={searchAll}
          icon={faSearch}
        >
          Search All
        </Toolbox.Button>
      </Toolbox>
      <QueryPageTable
        tableStyles={{ emptyText: `No missing ${name} subtitles` }}
        query={query}
        columns={columns}
      ></QueryPageTable>
    </Container>
  );
}

export default WantedView;
