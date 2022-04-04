import { useIsAnyActionRunning } from "@/apis/hooks";
import { UsePaginationQueryResult } from "@/apis/queries/hooks";
import { createAndDispatchTask } from "@/modules/task/utilities";
import { faSearch } from "@fortawesome/free-solid-svg-icons";
import { Container, Row } from "@mantine/core";
import { Helmet } from "react-helmet";
import { Column } from "react-table";
import { ContentHeader, QueryPageTable } from "..";

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
  // TODO
  const dataCount = query.paginationStatus.totalCount;
  const hasTask = useIsAnyActionRunning();

  return (
    <Container fluid>
      <Helmet>
        <title>Wanted {name} - Bazarr</title>
      </Helmet>
      <ContentHeader>
        <ContentHeader.Button
          disabled={hasTask || dataCount === 0}
          onClick={() => {
            createAndDispatchTask(name, "search-subtitles", searchAll);
          }}
          icon={faSearch}
        >
          Search All
        </ContentHeader.Button>
      </ContentHeader>
      <Row>
        <QueryPageTable
          emptyText={`No Missing ${name} Subtitles`}
          query={query}
          columns={columns}
          data={[]}
        ></QueryPageTable>
      </Row>
    </Container>
  );
}

export default WantedView;
