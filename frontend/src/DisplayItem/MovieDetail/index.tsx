import {
  faCloudUploadAlt,
  faHistory,
  faSearch,
  faSync,
  faToolbox,
  faUser,
  faWrench,
} from "@fortawesome/free-solid-svg-icons";
import React, { FunctionComponent, useCallback, useState } from "react";
import { Alert, Container, Row } from "react-bootstrap";
import { Helmet } from "react-helmet";
import { Redirect, RouteComponentProps, withRouter } from "react-router-dom";
import { useDownloadMovieSubtitles } from "src/apis/hooks";
import { useLanguageProfileBy } from "src/utilities/languages";
import { dispatchTask } from "../../@modules/task";
import { useIsAnyTaskRunningWithId } from "../../@modules/task/hooks";
import { createTask } from "../../@modules/task/utilities";
import {
  useMovieAction,
  useMovieById,
  useMovieModification,
} from "../../apis/hooks/movies";
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
import ItemOverview from "../generic/ItemOverview";
import Table from "./table";

interface Params {
  id: string;
}

interface Props extends RouteComponentProps<Params> {}

const MovieDetailView: FunctionComponent<Props> = ({ match }) => {
  const id = Number.parseInt(match.params.id);
  const { data: movie } = useMovieById(id);

  const profile = useLanguageProfileBy(movie?.profileId);

  const showModal = useShowModal();

  const { mutateAsync } = useMovieModification();
  const { mutateAsync: action } = useMovieAction();
  const { mutateAsync: downloadAsync } = useDownloadMovieSubtitles();

  const download = useCallback(
    (item: Item.Movie, result: SearchResultType) => {
      const {
        language,
        hearing_impaired: hi,
        forced,
        provider,
        subtitle,
      } = result;
      const { radarrId } = item;

      return downloadAsync({
        radarrId,
        form: {
          language,
          hi,
          forced,
          provider,
          subtitle,
        },
      });
    },
    [downloadAsync]
  );

  const [valid, setValid] = useState(true);

  const hasTask = useIsAnyTaskRunningWithId([id]);

  if (isNaN(id) || !valid) {
    return <Redirect to={RouterEmptyPath}></Redirect>;
  }

  if (!movie) {
    return <LoadingIndicator></LoadingIndicator>;
  }

  const allowEdit = movie.profileId !== undefined;

  return (
    <Container fluid>
      <Helmet>
        <title>{movie.title} - Bazarr (Movies)</title>
      </Helmet>
      <ContentHeader>
        <ContentHeader.Group pos="start">
          <ContentHeader.Button
            icon={faSync}
            disabled={hasTask}
            onClick={() => {
              const task = createTask(movie.title, id, action, {
                action: "scan-disk",
                radarrid: id,
              });
              dispatchTask("Scanning Disk...", [task], "Scanning...");
            }}
          >
            Scan Disk
          </ContentHeader.Button>
          <ContentHeader.Button
            icon={faSearch}
            disabled={movie.profileId === null}
            onClick={() => {
              const task = createTask(movie.title, id, action, {
                action: "search-missing",
                radarrid: id,
              });
              dispatchTask("Searching subtitles...", [task], "Searching...");
            }}
          >
            Search
          </ContentHeader.Button>
          <ContentHeader.Button
            icon={faUser}
            disabled={movie.profileId === null || hasTask}
            onClick={() => showModal<Item.Movie>("manual-search", movie)}
          >
            Manual
          </ContentHeader.Button>
          <ContentHeader.Button
            icon={faHistory}
            onClick={() => showModal("history", movie)}
          >
            History
          </ContentHeader.Button>
          <ContentHeader.Button
            icon={faToolbox}
            disabled={hasTask}
            onClick={() => showModal("tools", [movie])}
          >
            Tools
          </ContentHeader.Button>
        </ContentHeader.Group>

        <ContentHeader.Group pos="end">
          <ContentHeader.Button
            disabled={!allowEdit || movie.profileId === null || hasTask}
            icon={faCloudUploadAlt}
            onClick={() => showModal("upload", movie)}
          >
            Upload
          </ContentHeader.Button>
          <ContentHeader.Button
            icon={faWrench}
            disabled={hasTask}
            onClick={() => showModal("edit", movie)}
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
        <ItemOverview item={movie} details={[]}></ItemOverview>
      </Row>
      <Row>
        <Table movie={movie} profile={profile} disabled={hasTask}></Table>
      </Row>
      <ItemEditorModal modalKey="edit" submit={mutateAsync}></ItemEditorModal>
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
