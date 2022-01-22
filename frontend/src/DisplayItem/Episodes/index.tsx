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
import { useLanguageProfileBy } from "src/utilities/languages";
import { dispatchTask } from "../../@modules/task";
import { useIsAnyTaskRunningWithId } from "../../@modules/task/hooks";
import { createTask } from "../../@modules/task/utilities";
import {
  useEpisodeBySeriesId,
  useSeriesAction,
  useSeriesById,
  useSeriesModification,
} from "../../apis/hooks";
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
  const { data: series } = useSeriesById(id);
  const { data: episodes } = useEpisodeBySeriesId(id);

  const { mutateAsync } = useSeriesModification();
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

  const showModal = useShowModal();

  const [valid, setValid] = useState(true);

  const profile = useLanguageProfileBy(series?.profileId);

  const hasTask = useIsAnyTaskRunningWithId([
    ...(episodes?.map((v) => v.sonarrEpisodeId) ?? []),
    id,
  ]);

  if (isNaN(id) || !valid) {
    return <Redirect to={RouterEmptyPath}></Redirect>;
  }

  if (!series) {
    return <LoadingIndicator></LoadingIndicator>;
  }

  return (
    <Container fluid>
      <Helmet>
        <title>{series.title} - Bazarr (Series)</title>
      </Helmet>
      <ContentHeader>
        <ContentHeader.Group pos="start">
          <ContentHeader.Button
            icon={faSync}
            disabled={!available || hasTask}
            onClick={() => {
              const task = createTask(series.title, id, action, {
                action: "scan-disk",
                seriesid: id,
              });
              dispatchTask("Scanning disk...", [task], "Scanning...");
            }}
          >
            Scan Disk
          </ContentHeader.Button>
          <ContentHeader.Button
            icon={faSearch}
            onClick={() => {
              const task = createTask(series.title, id, action, {
                action: "search-missing",
                seriesid: id,
              });
              dispatchTask("Searching subtitles...", [task], "Searching...");
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
            onClick={() => showModal("tools", episodes)}
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
            onClick={() => showModal("upload", series)}
          >
            Upload
          </ContentHeader.Button>
          <ContentHeader.Button
            icon={faWrench}
            disabled={hasTask}
            onClick={() => showModal("edit", series)}
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
        <ItemOverview item={series} details={details}></ItemOverview>
      </Row>
      <Row>
        <Table
          series={series}
          episodes={episodes ?? []}
          profile={profile}
          disabled={hasTask}
        ></Table>
      </Row>
      <ItemEditorModal modalKey="edit" submit={mutateAsync}></ItemEditorModal>
      <SeriesUploadModal
        modalKey="upload"
        episodes={episodes ?? []}
      ></SeriesUploadModal>
    </Container>
  );
};

export default withRouter(SeriesEpisodesView);
