import {
  useEpisodesBySeriesId,
  useIsAnyActionRunning,
  useSeriesAction,
  useSeriesById,
  useSeriesModification,
} from "@/apis/hooks";
import { ContentHeader, LoadingIndicator } from "@/components";
import ItemOverview from "@/components/ItemOverview";
import { ItemEditorModal, SeriesUploadModal } from "@/components/modals";
import { SubtitleToolModal } from "@/components/modals/subtitle-tools";
import { useModalControl } from "@/modules/modals";
import { createAndDispatchTask } from "@/modules/task/utilities";
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
import { Container, Stack } from "@mantine/core";
import { FunctionComponent, useMemo } from "react";
import { Helmet } from "react-helmet";
import { Navigate, useParams } from "react-router-dom";
import Table from "./table";

const SeriesEpisodesView: FunctionComponent = () => {
  const params = useParams();
  const id = Number.parseInt(params.id as string);
  const { data: series, isFetched } = useSeriesById(id);
  const { data: episodes } = useEpisodesBySeriesId(id);

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

  const { show } = useModalControl();

  const profile = useLanguageProfileBy(series?.profileId);

  const hasTask = useIsAnyActionRunning();

  if (isNaN(id) || (isFetched && !series)) {
    return <Navigate to="/not-found"></Navigate>;
  }

  if (!series) {
    return <LoadingIndicator></LoadingIndicator>;
  }

  return (
    <Container px={0} fluid>
      <Helmet>
        <title>{series.title} - Bazarr (Series)</title>
      </Helmet>
      <ContentHeader>
        <ContentHeader.Group pos="start">
          <ContentHeader.Button
            icon={faSync}
            disabled={!available || hasTask}
            onClick={() => {
              createAndDispatchTask(series.title, "scan-disk", action, {
                action: "scan-disk",
                seriesid: id,
              });
            }}
          >
            Scan Disk
          </ContentHeader.Button>
          <ContentHeader.Button
            icon={faSearch}
            onClick={() => {
              createAndDispatchTask(series.title, "search-subtitles", action, {
                action: "search-missing",
                seriesid: id,
              });
            }}
            disabled={
              series.episodeFileCount === 0 ||
              series.profileId === null ||
              !available
            }
          >
            Search
          </ContentHeader.Button>
        </ContentHeader.Group>
        <ContentHeader.Group pos="end">
          <ContentHeader.Button
            disabled={series.episodeFileCount === 0 || !available || hasTask}
            icon={faBriefcase}
            onClick={() => show(SubtitleToolModal, episodes)}
          >
            Tools
          </ContentHeader.Button>
          <ContentHeader.Button
            disabled={
              series.episodeFileCount === 0 ||
              series.profileId === null ||
              !available
            }
            icon={faCloudUploadAlt}
            onClick={() => show(SeriesUploadModal, series)}
          >
            Upload
          </ContentHeader.Button>
          <ContentHeader.Button
            icon={faWrench}
            disabled={hasTask}
            onClick={() => show(ItemEditorModal, series)}
          >
            Edit Series
          </ContentHeader.Button>
        </ContentHeader.Group>
      </ContentHeader>

      <Stack>
        <ItemOverview item={series} details={details}></ItemOverview>
        {episodes === undefined ? (
          <LoadingIndicator></LoadingIndicator>
        ) : (
          <Table
            series={series}
            episodes={episodes}
            profile={profile}
            disabled={hasTask}
          ></Table>
        )}
      </Stack>
      <ItemEditorModal mutation={mutation}></ItemEditorModal>
      <SeriesUploadModal episodes={episodes ?? []}></SeriesUploadModal>
    </Container>
  );
};

export default SeriesEpisodesView;
