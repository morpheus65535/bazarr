import { useIsAnyActionRunning } from "@/apis/hooks";
import { UsePaginationQueryResult } from "@/apis/queries/hooks";
import { createAndDispatchTask } from "@/modules/task/utilities";
import { faSearch } from "@fortawesome/free-solid-svg-icons";
import { Container } from "@mantine/core";
import { Helmet } from "react-helmet";
import { Column } from "react-table";
import { QueryPageTable, Toolbox } from "..";

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

  return (
    <Container fluid px={0}>
      <Helmet>
        <title>Wanted {name} - Bazarr</title>
      </Helmet>
      <Toolbox>
        <Toolbox.Button
          disabled={hasTask || dataCount === 0}
          onClick={() => {
            createAndDispatchTask(name, "search-subtitles", searchAll);
          }}
          icon={faSearch}
        >
          Search All
        </Toolbox.Button>
      </Toolbox>
      <QueryPageTable
        emptyText={`No Missing ${name} Subtitles`}
        query={query}
        columns={columns}
        data={[]}
      ></QueryPageTable>
    </Container>
  );
}

export default WantedView;
