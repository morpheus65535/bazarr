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
import { useEpisodesBy, useProfileBy, useSerieBy } from "../../@redux/hooks";
import { SeriesApi } from "../../apis";
import {
  ContentHeader,
  ItemEditorModal,
  LoadingIndicator,
  SeriesUploadModal,
  useShowModal,
} from "../../components";
import { RouterEmptyPath } from "../../special-pages/404";
import { useOnLoadedOnce } from "../../utilities";
import ItemOverview from "../generic/ItemOverview";
import Table from "./table";

interface Params {
  id: string;
}

interface Props extends RouteComponentProps<Params> {}

const SeriesEpisodesView: FunctionComponent<Props> = (props) => {
  const { match } = props;
  const id = Number.parseInt(match.params.id);
  const series = useSerieBy(id);
  const episodes = useEpisodesBy(id);
  const serie = series.content;

  const available = episodes.content.length !== 0;

  const details = useMemo(
    () => [
      {
        icon: faHdd,
        text: `${serie?.episodeFileCount} files`,
      },
      {
        icon: faAdjust,
        text: serie?.seriesType ?? "",
      },
    ],
    [serie]
  );

  const showModal = useShowModal();

  const [valid, setValid] = useState(true);

  useOnLoadedOnce(() => {
    if (series.content === null) {
      setValid(false);
    }
  }, series);

  const profile = useProfileBy(series.content?.profileId);

  const hasTask = useIsAnyTaskRunningWithId([
    ...episodes.content.map((v) => v.sonarrEpisodeId),
    id,
  ]);

  if (isNaN(id) || !valid) {
    return <Redirect to={RouterEmptyPath}></Redirect>;
  }

  if (!serie) {
    return <LoadingIndicator></LoadingIndicator>;
  }

  return (
    <Container fluid>
      <Helmet>
        <title>{serie.title} - Bazarr (Series)</title>
      </Helmet>
      <ContentHeader>
        <ContentHeader.Group pos="start">
          <ContentHeader.Button
            icon={faSync}
            disabled={!available || hasTask}
            onClick={() => {
              const task = createTask(
                serie.title,
                id,
                SeriesApi.action.bind(SeriesApi),
                {
                  action: "scan-disk",
                  seriesid: id,
                }
              );
              dispatchTask("Scaning disk...", [task], "Scaning...");
            }}
          >
            Scan Disk
          </ContentHeader.Button>
          <ContentHeader.Button
            icon={faSearch}
            onClick={() => {
              const task = createTask(
                serie.title,
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
              serie.episodeFileCount === 0 ||
              serie.profileId === null ||
              !available
            }
          >
            Search
          </ContentHeader.Button>
        </ContentHeader.Group>
        <ContentHeader.Group pos="end">
          <ContentHeader.Button
            disabled={serie.episodeFileCount === 0 || !available || hasTask}
            icon={faBriefcase}
            onClick={() => showModal("tools", episodes.content)}
          >
            Tools
          </ContentHeader.Button>
          <ContentHeader.Button
            disabled={
              serie.episodeFileCount === 0 ||
              serie.profileId === null ||
              !available
            }
            icon={faCloudUploadAlt}
            onClick={() => showModal("upload", serie)}
          >
            Upload
          </ContentHeader.Button>
          <ContentHeader.Button
            icon={faWrench}
            disabled={hasTask}
            onClick={() => showModal("edit", serie)}
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
        <ItemOverview item={serie} details={details}></ItemOverview>
      </Row>
      <Row>
        <Table
          serie={series}
          episodes={episodes}
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
        episodes={episodes.content}
      ></SeriesUploadModal>
    </Container>
  );
};

export default withRouter(SeriesEpisodesView);
