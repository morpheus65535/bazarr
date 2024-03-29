import { useIsAnyActionRunning } from "@/apis/hooks";
import { UsePaginationQueryResult } from "@/apis/queries/hooks";
import { QueryPageTable, Toolbox } from "@/components";
import { faSearch } from "@fortawesome/free-solid-svg-icons";
import { Container } from "@mantine/core";
import { useDocumentTitle } from "@mantine/hooks";
import { Column } from "react-table";

interface Props<T extends Wanted.Base> {
  name: string;
  columns: Column<T>[];
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

  useDocumentTitle(`Wanted ${name} - Bazarr`);

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
