import {
  useEpisodesBySeriesId,
  useIsAnyActionRunning,
  useSeriesAction,
  useSeriesById,
  useSeriesModification,
} from "@/apis/hooks";
import { Toolbox } from "@/components";
import { QueryOverlay } from "@/components/async";
import ItemEditForm from "@/components/forms/ItemEditForm";
import ItemOverview from "@/components/ItemOverview";
import { SeriesUploadModal } from "@/components/modals";
import { SubtitleToolModal } from "@/components/modals/subtitle-tools";
import { useModals } from "@/modules/modals";
import { createAndDispatchTask } from "@/modules/task";
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
import { Container, Group, Popover, Stack } from "@mantine/core";
import { FunctionComponent, useMemo, useState } from "react";
import { Helmet } from "react-helmet";
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

  const [isEditing, setIsEditing] = useState(false);

  if (isNaN(id) || (isFetched && !series)) {
    return <Navigate to="/not-found"></Navigate>;
  }

  return (
    <Container px={0} fluid>
      <QueryOverlay result={seriesQuery}>
        <Helmet>
          <title>{series?.title ?? "Unknown Series"} - Bazarr (Series)</title>
        </Helmet>
        <Toolbox>
          <Group spacing="xs">
            <Toolbox.Button
              icon={faSync}
              disabled={!available || hasTask}
              onClick={() => {
                if (series) {
                  createAndDispatchTask(series.title, "scan-disk", action, {
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
                  createAndDispatchTask(
                    series.title,
                    "search-subtitles",
                    action,
                    {
                      action: "search-missing",
                      seriesid: id,
                    }
                  );
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
                  modals.openContextModal(SubtitleToolModal, {
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
              onClick={() => {
                if (series) {
                  modals.openContextModal(SeriesUploadModal, {
                    payload: series,
                  });
                }
              }}
            >
              Upload
            </Toolbox.Button>
            <Popover
              opened={isEditing}
              onClose={() => setIsEditing(false)}
              placement="end"
              title="Edit Series"
              transition="scale"
              target={
                <Toolbox.Button
                  icon={faWrench}
                  disabled={hasTask}
                  onClick={() => setIsEditing(true)}
                >
                  Edit Series
                </Toolbox.Button>
              }
            >
              <ItemEditForm
                mutation={mutation}
                item={series ?? null}
                onCancel={() => setIsEditing(false)}
                onComplete={() => setIsEditing(false)}
              ></ItemEditForm>
            </Popover>
          </Group>
        </Toolbox>
        <Stack>
          <ItemOverview item={series ?? null} details={details}></ItemOverview>
          <QueryOverlay result={episodesQuery}>
            <Table
              series={series}
              episodes={episodes ?? []}
              profile={profile}
              disabled={hasTask}
            ></Table>
          </QueryOverlay>
        </Stack>
      </QueryOverlay>
    </Container>
  );
};

export default SeriesEpisodesView;
