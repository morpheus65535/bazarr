import { faSearch } from "@fortawesome/free-solid-svg-icons";
import React from "react";
import { Container, Row } from "react-bootstrap";
import { Helmet } from "react-helmet";
import { Column } from "react-table";
import { useIsAnyActionRunning } from "src/apis/hooks";
import { dispatchTask } from "../../@modules/task";
import { createTask } from "../../@modules/task/utilities";
import { AsyncPageTable, ContentHeader } from "../../components";

interface Props<T extends Wanted.Base> {
  name: string;
  keys: string[];
  columns: Column<T>[];
  query: RangeQuery<T>;
  searchAll: () => Promise<void>;
}

const TaskGroupName = "Searching wanted subtitles...";

function GenericWantedView<T extends Wanted.Base>({
  name,
  keys,
  columns,
  query,
  searchAll,
}: Props<T>) {
  // TODO
  const dataCount = 0;

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
        <AsyncPageTable
          emptyText={`No Missing ${name} Subtitles`}
          keys={keys}
          query={query}
          columns={columns}
          data={[]}
        ></AsyncPageTable>
      </Row>
    </Container>
  );
}

export default GenericWantedView;
