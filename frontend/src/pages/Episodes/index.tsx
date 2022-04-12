import {
  useEpisodesBySeriesId,
  useIsAnyActionRunning,
  useSeriesAction,
  useSeriesById,
  useSeriesModification,
} from "@/apis/hooks";
import { Toolbox } from "@/components";
import { QueryOverlay } from "@/components/async";
import { ItemEditModal } from "@/components/forms/ItemEditForm";
import { SeriesUploadModal } from "@/components/forms/SeriesUploadForm";
import File, { FileOverlay } from "@/components/inputs/File";
import { SubtitleToolsModal } from "@/components/modals";
import { useModals } from "@/modules/modals";
import { task, TaskGroup } from "@/modules/task";
import ItemOverview from "@/pages/views/ItemOverview";
import { useLanguageProfileBy } from "@/utilities/languages";
import {
  faAdjust,
  faBriefcase,
  faCloudUploadAlt,
  faHdd,
  faSearch,
  faSync,
  faWrench,
} from "@fortawesome/free-solid-svg-icons";
import { Container, Group, Stack } from "@mantine/core";
import { useDocumentTitle } from "@mantine/hooks";
import { FunctionComponent, useCallback, useMemo, useRef } from "react";
import { Navigate, useParams } from "react-router-dom";
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
        icon: faAdjust,
        text: series?.seriesType ?? "",
      },
    ],
    [series]
  );

  const modals = useModals();

  const profile = useLanguageProfileBy(series?.profileId);

  const hasTask = useIsAnyActionRunning();

  const dialogRef = useRef<VoidFunction>(null);
  const onDrop = useCallback(
    (files: File[]) => {
      if (series && profile) {
        modals.openContextModal(SeriesUploadModal, {
          files,
          series,
        });
      }
    },
    [modals, profile, series]
  );

  useDocumentTitle(`${series?.title ?? "Unknown Series"} - Bazarr (Series)`);

  if (isNaN(id) || (isFetched && !series)) {
    return <Navigate to="/not-found"></Navigate>;
  }

  return (
    <Container px={0} fluid>
      <QueryOverlay result={seriesQuery}>
        <FileOverlay
          disabled={profile === undefined}
          accept={[""]}
          onDrop={onDrop}
        ></FileOverlay>
        <div hidden>
          {/* A workaround to allow click to upload files */}
          <File
            disabled={profile === undefined}
            accept={[""]}
            openRef={dialogRef}
            onDrop={onDrop}
          ></File>
        </div>
        <Toolbox>
          <Group spacing="xs">
            <Toolbox.Button
              icon={faSync}
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
              onClick={() => {
                if (series) {
                  task.create(series.title, TaskGroup.SearchSubtitle, action, {
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
            >
              Search
            </Toolbox.Button>
          </Group>
          <Group spacing="xs">
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
              Tools
            </Toolbox.Button>
            <Toolbox.Button
              disabled={
                series === undefined ||
                series.episodeFileCount === 0 ||
                series.profileId === null ||
                !available
              }
              icon={faCloudUploadAlt}
              onClick={() => dialogRef.current?.()}
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
                    { title: series.title }
                  );
                }
              }}
            >
              Edit Series
            </Toolbox.Button>
          </Group>
        </Toolbox>
        <Stack>
          <ItemOverview item={series ?? null} details={details}></ItemOverview>
          <QueryOverlay result={episodesQuery}>
            <Table
              episodes={episodes ?? null}
              profile={profile}
              disabled={hasTask || !series || series.profileId === null}
            ></Table>
          </QueryOverlay>
        </Stack>
      </QueryOverlay>
    </Container>
  );
};

export default SeriesEpisodesView;
