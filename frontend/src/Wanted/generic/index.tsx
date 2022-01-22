import { faSearch } from "@fortawesome/free-solid-svg-icons";
import React from "react";
import { Container, Row } from "react-bootstrap";
import { Helmet } from "react-helmet";
import { Column } from "react-table";
import { useIsAnyActionRunning } from "src/apis/hooks";
import { PaginationQuery } from "src/apis/queries/hooks";
import { dispatchTask } from "../../@modules/task";
import { createTask } from "../../@modules/task/utilities";
import { ContentHeader, QueryPageTable } from "../../components";

interface Props<T extends Wanted.Base> {
  name: string;
  columns: Column<T>[];
  query: PaginationQuery<T>;
  searchAll: () => Promise<void>;
}

const TaskGroupName = "Searching wanted subtitles...";

function GenericWantedView<T extends Wanted.Base>({
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
            const task = createTask(name, undefined, searchAll);
            dispatchTask(TaskGroupName, [task], "Searching...");
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

export default GenericWantedView;
