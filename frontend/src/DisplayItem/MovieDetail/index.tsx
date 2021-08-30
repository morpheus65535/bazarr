import {
  faCloudUploadAlt,
  faHistory,
  faSearch,
  faSync,
  faToolbox,
  faUser,
  faWrench,
} from "@fortawesome/free-solid-svg-icons";
import React, { FunctionComponent, useState } from "react";
import { Alert, Container, Row } from "react-bootstrap";
import { Helmet } from "react-helmet";
import { Redirect, RouteComponentProps, withRouter } from "react-router-dom";
import { dispatchTask } from "../../@modules/task";
import { useIsAnyTaskRunningWithId } from "../../@modules/task/hooks";
import { createTask } from "../../@modules/task/utilities";
import { useMovieBy, useProfileBy } from "../../@redux/hooks";
import { MoviesApi, ProvidersApi } from "../../apis";
import {
  ContentHeader,
  ItemEditorModal,
  LoadingIndicator,
  MovieHistoryModal,
  MovieUploadModal,
  SubtitleToolModal,
  useShowModal,
} from "../../components";
import { ManualSearchModal } from "../../components/modals/ManualSearchModal";
import { RouterEmptyPath } from "../../special-pages/404";
import { useOnLoadedOnce } from "../../utilities";
import ItemOverview from "../generic/ItemOverview";
import Table from "./table";

const download = (item: Item.Movie, result: SearchResultType) => {
  const { language, hearing_impaired, forced, provider, subtitle } = result;
  return ProvidersApi.downloadMovieSubtitle(item.radarrId, {
    language,
    hi: hearing_impaired,
    forced,
    provider,
    subtitle,
  });
};

interface Params {
  id: string;
}

interface Props extends RouteComponentProps<Params> {}

const MovieDetailView: FunctionComponent<Props> = ({ match }) => {
  const id = Number.parseInt(match.params.id);
  const movie = useMovieBy(id);
  const item = movie.content;

  const profile = useProfileBy(movie.content?.profileId);

  const showModal = useShowModal();

  const [valid, setValid] = useState(true);

  const hasTask = useIsAnyTaskRunningWithId([id]);

  useOnLoadedOnce(() => {
    if (movie.content === null) {
      setValid(false);
    }
  }, movie);

  if (isNaN(id) || !valid) {
    return <Redirect to={RouterEmptyPath}></Redirect>;
  }

  if (!item) {
    return <LoadingIndicator></LoadingIndicator>;
  }

  const allowEdit = item.profileId !== undefined;

  return (
    <Container fluid>
      <Helmet>
        <title>{item.title} - Bazarr (Movies)</title>
      </Helmet>
      <ContentHeader>
        <ContentHeader.Group pos="start">
          <ContentHeader.Button
            icon={faSync}
            disabled={hasTask}
            onClick={() => {
              const task = createTask(
                item.title,
                id,
                MoviesApi.action.bind(MoviesApi),
                { action: "scan-disk", radarrid: id }
              );
              dispatchTask("Scaning Disk...", [task], "Scaning...");
            }}
          >
            Scan Disk
          </ContentHeader.Button>
          <ContentHeader.Button
            icon={faSearch}
            disabled={item.profileId === null}
            onClick={() => {
              const task = createTask(
                item.title,
                id,
                MoviesApi.action.bind(MoviesApi),
                {
                  action: "search-missing",
                  radarrid: id,
                }
              );
              dispatchTask("Searching subtitles...", [task], "Searching...");
            }}
          >
            Search
          </ContentHeader.Button>
          <ContentHeader.Button
            icon={faUser}
            disabled={item.profileId === null || hasTask}
            onClick={() => showModal<Item.Movie>("manual-search", item)}
          >
            Manual
          </ContentHeader.Button>
          <ContentHeader.Button
            icon={faHistory}
            onClick={() => showModal("history", item)}
          >
            History
          </ContentHeader.Button>
          <ContentHeader.Button
            icon={faToolbox}
            disabled={hasTask}
            onClick={() => showModal("tools", [item])}
          >
            Tools
          </ContentHeader.Button>
        </ContentHeader.Group>

        <ContentHeader.Group pos="end">
          <ContentHeader.Button
            disabled={!allowEdit || item.profileId === null || hasTask}
            icon={faCloudUploadAlt}
            onClick={() => showModal("upload", item)}
          >
            Upload
          </ContentHeader.Button>
          <ContentHeader.Button
            icon={faWrench}
            disabled={hasTask}
            onClick={() => showModal("edit", item)}
          >
            Edit Movie
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
          A background task is running for this movie, actions are unavailable
        </Alert>
      </Row>
      <Row>
        <ItemOverview item={item} details={[]}></ItemOverview>
      </Row>
      <Row>
        <Table movie={item} profile={profile} disabled={hasTask}></Table>
      </Row>
      <ItemEditorModal
        modalKey="edit"
        submit={(form) => MoviesApi.modify(form)}
      ></ItemEditorModal>
      <SubtitleToolModal modalKey="tools" size="lg"></SubtitleToolModal>
      <MovieHistoryModal modalKey="history" size="lg"></MovieHistoryModal>
      <MovieUploadModal modalKey="upload" size="lg"></MovieUploadModal>
      <ManualSearchModal
        modalKey="manual-search"
        download={download}
      ></ManualSearchModal>
    </Container>
  );
};

export default withRouter(MovieDetailView);
