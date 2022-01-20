import { faSearch } from "@fortawesome/free-solid-svg-icons";
import { capitalize } from "lodash";
import React from "react";
import { Container, Row } from "react-bootstrap";
import { Helmet } from "react-helmet";
import { Column } from "react-table";
import { dispatchTask } from "../../@modules/task";
import { useIsGroupTaskRunning } from "../../@modules/task/hooks";
import { createTask } from "../../@modules/task/utilities";
import { AsyncPageTable, ContentHeader } from "../../components";

interface Props<T extends Wanted.Base> {
  type: "movies" | "series";
  columns: Column<T>[];
  query: RangeQuery<T>;
  searchAll: () => Promise<void>;
}

const TaskGroupName = "Searching wanted subtitles...";

function GenericWantedView<T extends Wanted.Base>({
  type,
  columns,
  query,
  searchAll,
}: Props<T>) {
  const typeName = capitalize(type);

  // TODO
  const dataCount = 1;

  const hasTask = useIsGroupTaskRunning(TaskGroupName);

  return (
    <Container fluid>
      <Helmet>
        <title>Wanted {typeName} - Bazarr</title>
      </Helmet>
      <ContentHeader>
        <ContentHeader.Button
          // disabled={dataCount === 0 || hasTask}
          onClick={() => {
            const task = createTask(type, undefined, searchAll);
            dispatchTask(TaskGroupName, [task], "Searching...");
          }}
          icon={faSearch}
        >
          Search All
        </ContentHeader.Button>
      </ContentHeader>
      <Row>
        <AsyncPageTable
          emptyText={`No Missing ${typeName} Subtitles`}
          keys={[`${type}-wanted`]}
          query={query}
          columns={columns}
          data={[]}
        ></AsyncPageTable>
      </Row>
    </Container>
  );
}

export default GenericWantedView;
