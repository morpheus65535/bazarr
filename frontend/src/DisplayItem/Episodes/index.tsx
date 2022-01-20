import {
  faAdjust,
  faBriefcase,
  faCloudUploadAlt,
  faHdd,
  faSearch,
  faSync,
  faWrench,
} from "@fortawesome/free-solid-svg-icons";
import React, { FunctionComponent, useMemo, useState } from "react";
import { Alert, Container, Row } from "react-bootstrap";
import { Helmet } from "react-helmet";
import { Redirect, RouteComponentProps, withRouter } from "react-router-dom";
import { dispatchTask } from "../../@modules/task";
import { useIsAnyTaskRunningWithId } from "../../@modules/task/hooks";
import { createTask } from "../../@modules/task/utilities";
import { useProfileBy } from "../../@redux/hooks";
import { SeriesApi } from "../../apis";
import { useEpisodeBySeriesId, useSeriesByIds } from "../../apis/hooks/series";
import {
  ContentHeader,
  ItemEditorModal,
  LoadingIndicator,
  SeriesUploadModal,
  useShowModal,
} from "../../components";
import { RouterEmptyPath } from "../../special-pages/404";
import ItemOverview from "../generic/ItemOverview";
import Table from "./table";

interface Params {
  id: string;
}

interface Props extends RouteComponentProps<Params> {}

const SeriesEpisodesView: FunctionComponent<Props> = (props) => {
  const { match } = props;
  const id = Number.parseInt(match.params.id);
  const { data: series } = useSeriesByIds([id]);
  const { data: episodes } = useEpisodeBySeriesId([id]);

  const tvShow = (series?.data.length ?? -1) > 0 ? series?.data[0] : undefined;

  const available = episodes?.length !== 0;

  const details = useMemo(
    () => [
      {
        icon: faHdd,
        text: `${tvShow?.episodeFileCount} files`,
      },
      {
        icon: faAdjust,
        text: tvShow?.seriesType ?? "",
      },
    ],
    [tvShow]
  );

  const showModal = useShowModal();

  const [valid, setValid] = useState(true);

  const profile = useProfileBy(tvShow?.profileId);

  const hasTask = useIsAnyTaskRunningWithId([
    ...(episodes?.map((v) => v.sonarrEpisodeId) ?? []),
    id,
  ]);

  if (isNaN(id) || !valid) {
    return <Redirect to={RouterEmptyPath}></Redirect>;
  }

  if (!tvShow) {
    return <LoadingIndicator></LoadingIndicator>;
  }

  return (
    <Container fluid>
      <Helmet>
        <title>{tvShow.title} - Bazarr (Series)</title>
      </Helmet>
      <ContentHeader>
        <ContentHeader.Group pos="start">
          <ContentHeader.Button
            icon={faSync}
            disabled={!available || hasTask}
            onClick={() => {
              const task = createTask(
                tvShow.title,
                id,
                SeriesApi.action.bind(SeriesApi),
                {
                  action: "scan-disk",
                  seriesid: id,
                }
              );
              dispatchTask("Scanning disk...", [task], "Scanning...");
            }}
          >
            Scan Disk
          </ContentHeader.Button>
          <ContentHeader.Button
            icon={faSearch}
            onClick={() => {
              const task = createTask(
                tvShow.title,
                id,
                SeriesApi.action.bind(SeriesApi),
                {
                  action: "search-missing",
                  seriesid: id,
                }
              );
              dispatchTask("Searching subtitles...", [task], "Searching...");
            }}
            disabled={
              tvShow.episodeFileCount === 0 ||
              tvShow.profileId === null ||
              !available
            }
          >
            Search
          </ContentHeader.Button>
        </ContentHeader.Group>
        <ContentHeader.Group pos="end">
          <ContentHeader.Button
            disabled={tvShow.episodeFileCount === 0 || !available || hasTask}
            icon={faBriefcase}
            onClick={() => showModal("tools", episodes)}
          >
            Tools
          </ContentHeader.Button>
          <ContentHeader.Button
            disabled={
              tvShow.episodeFileCount === 0 ||
              tvShow.profileId === null ||
              !available
            }
            icon={faCloudUploadAlt}
            onClick={() => showModal("upload", tvShow)}
          >
            Upload
          </ContentHeader.Button>
          <ContentHeader.Button
            icon={faWrench}
            disabled={hasTask}
            onClick={() => showModal("edit", tvShow)}
          >
            Edit Series
          </ContentHeader.Button>
        </ContentHeader.Group>
      </ContentHeader>
      <Row>
        <Alert
          className="w-100 m-0 py-2"
          show={hasTask}
          style={{ borderRadius: 0 }}
          variant="light"
        >
          A background task is running for this show, actions are unavailable
        </Alert>
      </Row>
      <Row>
        <ItemOverview item={tvShow} details={details}></ItemOverview>
      </Row>
      <Row>
        <Table
          tvShow={tvShow}
          episodes={episodes ?? []}
          profile={profile}
          disabled={hasTask}
        ></Table>
      </Row>
      <ItemEditorModal
        modalKey="edit"
        submit={(form) => SeriesApi.modify(form)}
      ></ItemEditorModal>
      <SeriesUploadModal
        modalKey="upload"
        episodes={episodes ?? []}
      ></SeriesUploadModal>
    </Container>
  );
};

export default withRouter(SeriesEpisodesView);
