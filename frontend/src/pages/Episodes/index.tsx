import {
  FunctionComponent,
  useCallback,
  useMemo,
  useRef,
  useState,
} from "react";
import { Navigate, useParams } from "react-router";
import { Container, Group, Stack } from "@mantine/core";
import { Dropzone } from "@mantine/dropzone";
import { useDocumentTitle } from "@mantine/hooks";
import { showNotification } from "@mantine/notifications";
import {
  faAdjust,
  faBriefcase,
  faCalendar,
  faCircleChevronDown,
  faCircleChevronRight,
  faCloudUploadAlt,
  faHardDrive,
  faHdd,
  faPlay,
  faSearch,
  faStop,
  faSync,
  faTriangleExclamation,
  faWrench,
} from "@fortawesome/free-solid-svg-icons";
import { Table as TableInstance } from "@tanstack/table-core/build/lib/types";
import {
  useEpisodesBySeriesId,
  useIsAnyActionRunning,
  useSeriesAction,
  useSeriesById,
  useSeriesModification,
} from "@/apis/hooks";
import { DropContent, Toolbox } from "@/components";
import { QueryOverlay } from "@/components/async";
import { ItemEditModal } from "@/components/forms/ItemEditForm";
import { SeriesUploadModal } from "@/components/forms/SeriesUploadForm";
import { SubtitleToolsModal } from "@/components/modals";
import { useModals } from "@/modules/modals";
import { notification, task, TaskGroup } from "@/modules/task";
import ItemOverview from "@/pages/views/ItemOverview";
import { RouterNames } from "@/Router/RouterNames";
import { useLanguageProfileBy } from "@/utilities/languages";
import Table from "./table";

const SeriesEpisodesView: FunctionComponent = () => {
  const params = useParams();
  const id = Number.parseInt(params.id as string);

  const seriesQuery = useSeriesById(id);
  const episodesQuery = useEpisodesBySeriesId(id);

  const { data: episodes } = episodesQuery;
  const { data: series, isFetched } = seriesQuery;

  const mutation = useSeriesModification();
  const { mutateAsync: action } = useSeriesAction();

  const available = episodes?.length !== 0;

  const details = useMemo(
    () => [
      {
        icon: faHdd,
        text: `${series?.episodeFileCount} files`,
      },
      {
        icon: faTriangleExclamation,
        text: `${series?.episodeMissingCount} missing subtitles`,
      },
      {
        icon: series?.ended ? faStop : faPlay,
        text: series?.ended ? "Ended" : "Continuing",
      },
      {
        icon: faCalendar,
        text: `Last ${series?.ended ? "aired on" : "known airdate"}: ${series?.lastAired}`,
      },
      {
        icon: faAdjust,
        text: series?.seriesType ?? "",
      },
    ],
    [series],
  );

  const modals = useModals();

  const profile = useLanguageProfileBy(series?.profileId);

  const hasTask = useIsAnyActionRunning();

  const onDrop = useCallback(
    (files: File[]) => {
      if (series && profile) {
        modals.openContextModal(SeriesUploadModal, {
          files,
          series,
        });
      } else {
        showNotification(
          notification.warn(
            "Cannot Upload Files",
            "series or language profile is not ready",
          ),
        );
      }
    },
    [modals, profile, series],
  );

  useDocumentTitle(`${series?.title ?? "Unknown Series"} - Bazarr (Series)`);

  const tableRef = useRef<TableInstance<Item.Episode> | null>(null);

  const [isAllRowExpanded, setIsAllRowExpanded] = useState(
    tableRef?.current?.getIsAllRowsExpanded(),
  );

  const openDropzone = useRef<VoidFunction>(null);

  if (isNaN(id) || (isFetched && !series)) {
    return <Navigate to={RouterNames.NotFound}></Navigate>;
  }

  return (
    <Container px={0} fluid>
      <QueryOverlay result={seriesQuery}>
        <Dropzone.FullScreen
          openRef={openDropzone}
          active={profile !== undefined}
          onDrop={onDrop}
        >
          <DropContent></DropContent>
        </Dropzone.FullScreen>
        <Toolbox>
          <Group gap="xs">
            <Toolbox.Button
              icon={faSync}
              disabled={!available || hasTask}
              onClick={async () => {
                if (series) {
                  await action({
                    action: "sync",
                    seriesid: id,
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
                if (series) {
                  task.create(series.title, TaskGroup.ScanDisk, action, {
                    action: "scan-disk",
                    seriesid: id,
                  });
                }
              }}
            >
              Scan Disk
            </Toolbox.Button>
            <Toolbox.Button
              icon={faSearch}
              onClick={async () => {
                if (series) {
                  await action({
                    action: "search-missing",
                    seriesid: id,
                  });
                }
              }}
              disabled={
                series === undefined ||
                series.episodeFileCount === 0 ||
                series.profileId === null ||
                !available
              }
              loading={hasTask}
            >
              Search
            </Toolbox.Button>
          </Group>
          <Group gap="xs">
            <Toolbox.Button
              disabled={
                series === undefined ||
                series.episodeFileCount === 0 ||
                !available ||
                hasTask
              }
              icon={faBriefcase}
              onClick={() => {
                if (episodes) {
                  modals.openContextModal(SubtitleToolsModal, {
                    payload: episodes,
                  });
                }
              }}
            >
              Mass Edit
            </Toolbox.Button>
            <Toolbox.Button
              disabled={
                series === undefined ||
                series.episodeFileCount === 0 ||
                series.profileId === null ||
                !available ||
                hasTask
              }
              icon={faCloudUploadAlt}
              onClick={() => openDropzone.current?.()}
            >
              Upload
            </Toolbox.Button>
            <Toolbox.Button
              icon={faWrench}
              disabled={hasTask}
              onClick={() => {
                if (series) {
                  modals.openContextModal(
                    ItemEditModal,
                    {
                      item: series,
                      mutation,
                    },
                    { title: series.title },
                  );
                }
              }}
            >
              Edit Series
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
          <ItemOverview item={series ?? null} details={details}></ItemOverview>
          <QueryOverlay result={episodesQuery}>
            <Table
              ref={tableRef}
              episodes={episodes ?? null}
              profile={profile}
              disabled={hasTask || !series || series.profileId === null}
              onAllRowsExpandedChanged={setIsAllRowExpanded}
            ></Table>
          </QueryOverlay>
        </Stack>
      </QueryOverlay>
    </Container>
  );
};

export default SeriesEpisodesView;
