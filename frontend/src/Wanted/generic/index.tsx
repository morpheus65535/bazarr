import { faSearch } from "@fortawesome/free-solid-svg-icons";
import { capitalize } from "lodash";
import React from "react";
import { Container, Row } from "react-bootstrap";
import { Helmet } from "react-helmet";
import { Column } from "react-table";
import { dispatchTask } from "../../@modules/task";
import { useIsGroupTaskRunning } from "../../@modules/task/hooks";
import { createTask } from "../../@modules/task/utilites";
import { AsyncPageTable, ContentHeader } from "../../components";

interface Props<T extends Wanted.Base> {
  type: "movies" | "series";
  columns: Column<T>[];
  state: Async.Entity<T>;
  loader: (params: Parameter.Range) => void;
  searchAll: () => Promise<void>;
}

const TaskGroupName = "Searching wanted subtitles...";

function GenericWantedView<T extends Wanted.Base>({
  type,
  columns,
  state,
  loader,
  searchAll,
}: Props<T>) {
  const typeName = capitalize(type);

  const dataCount = Object.keys(state.content.entities).length;

  const hasTask = useIsGroupTaskRunning(TaskGroupName);

  return (
    <Container fluid>
      <Helmet>
        <title>Wanted {typeName} - Bazarr</title>
      </Helmet>
      <ContentHeader>
        <ContentHeader.Button
          disabled={dataCount === 0 || hasTask}
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
          entity={state}
          loader={loader}
          emptyText={`No Missing ${typeName} Subtitles`}
          columns={columns}
          data={[]}
        ></AsyncPageTable>
      </Row>
    </Container>
  );
}

export default GenericWantedView;
