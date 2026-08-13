import { FunctionComponent, useMemo, useRef, useState } from "react";
import { Navigate, useParams } from "react-router";
import { Container, Group, Stack } from "@mantine/core";
import { useDocumentTitle } from "@mantine/hooks";
import {
  faCircleChevronDown,
  faCircleChevronRight,
  faHardDrive,
  faHdd,
  faSearch,
  faSync,
  faTriangleExclamation,
  faTrophy,
  faWrench,
} from "@fortawesome/free-solid-svg-icons";
import {
  useIsAnyActionRunning,
  useSportsEventsByLeagueId,
  useSportsLeagueAction,
  useSportsLeagueById,
  useSportsLeagueModification,
} from "@/apis/hooks";
import { useInstanceName } from "@/apis/hooks/site";
import { Toolbox } from "@/components";
import { QueryOverlay } from "@/components/async";
import { ItemEditModal } from "@/components/forms/ItemEditForm";
import { type AppTable as TableInstance } from "@/components/tables/features";
import { useModals } from "@/modules/modals";
import { task, TaskGroup } from "@/modules/task";
import ItemOverview from "@/pages/views/ItemOverview";
import { RouterNames } from "@/Router/RouterNames";
import { useLanguageProfileBy } from "@/utilities/languages";
import Table from "./table";

const SportsEventsView: FunctionComponent = () => {
  const params = useParams();
  const id = Number.parseInt(params.id as string);

  const leagueQuery = useSportsLeagueById(id);
  const eventsQuery = useSportsEventsByLeagueId(id);

  const { data: events } = eventsQuery;
  const { data: league, isFetched } = leagueQuery;

  const mutation = useSportsLeagueModification();
  const { mutateAsync: action } = useSportsLeagueAction();

  const available = events?.length !== 0;

  const details = useMemo(
    () => [
      {
        icon: faHdd,
        text: `${league?.episodeFileCount} files`,
      },
      {
        icon: faTriangleExclamation,
        text: `${league?.episodeMissingCount} missing subtitles`,
      },
      {
        icon: faTrophy,
        text: league?.sport ?? "",
      },
    ],
    [league],
  );

  const modals = useModals();

  const profile = useLanguageProfileBy(league?.profileId);

  const hasTask = useIsAnyActionRunning();

  useDocumentTitle(
    `${league?.title ?? "Unknown League"} - ${useInstanceName()} (Sports)`,
  );

  const tableRef = useRef<TableInstance<Item.SportsEvent> | null>(null);

  const [isAllRowExpanded, setIsAllRowExpanded] = useState(
    tableRef?.current?.getIsAllRowsExpanded(),
  );

  if (isNaN(id) || (isFetched && !league)) {
    return <Navigate to={RouterNames.NotFound}></Navigate>;
  }

  return (
    <Container px={0} fluid>
      <QueryOverlay result={leagueQuery}>
        <Toolbox>
          <Group gap="xs">
            <Toolbox.Button
              icon={faSync}
              disabled={!available || hasTask}
              onClick={async () => {
                if (league) {
                  await action({
                    action: "sync",
                    leagueId: id,
                  });
                }
              }}
            >
              Sync
            </Toolbox.Button>
            <Toolbox.Button
              icon={faHardDrive}
              disabled={!available || hasTask}
              onClick={() => {
                if (league) {
                  task.create(league.title, TaskGroup.ScanDisk, action, {
                    action: "scan-disk",
                    leagueId: id,
                  });
                }
              }}
            >
              Scan Disk
            </Toolbox.Button>
            <Toolbox.Button
              icon={faSearch}
              onClick={async () => {
                if (league) {
                  await action({
                    action: "search-missing",
                    leagueId: id,
                  });
                }
              }}
              disabled={
                league === undefined ||
                league.episodeFileCount === 0 ||
                league.profileId === null ||
                !available
              }
              loading={hasTask}
            >
              Search
            </Toolbox.Button>
          </Group>
          <Group gap="xs">
            <Toolbox.Button
              icon={faWrench}
              disabled={hasTask}
              onClick={() => {
                if (league) {
                  modals.openContextModal(
                    ItemEditModal,
                    {
                      item: league,
                      mutation,
                    },
                    { title: league.title },
                  );
                }
              }}
            >
              Edit League
            </Toolbox.Button>
            <Toolbox.Button
              icon={
                isAllRowExpanded ? faCircleChevronRight : faCircleChevronDown
              }
              onClick={() => {
                tableRef.current?.toggleAllRowsExpanded();
              }}
            >
              {isAllRowExpanded ? "Collapse All" : "Expand All"}
            </Toolbox.Button>
          </Group>
        </Toolbox>
        <Stack>
          <ItemOverview item={league ?? null} details={details}></ItemOverview>
          <QueryOverlay result={eventsQuery}>
            <Table
              ref={tableRef}
              events={events ?? null}
              profile={profile}
              disabled={hasTask || !league || league.profileId === null}
              onAllRowsExpandedChanged={setIsAllRowExpanded}
            ></Table>
          </QueryOverlay>
        </Stack>
      </QueryOverlay>
    </Container>
  );
};

export default SportsEventsView;
