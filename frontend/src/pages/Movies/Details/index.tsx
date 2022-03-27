import {
  useDownloadMovieSubtitles,
  useIsMovieActionRunning,
  useMoviesProvider,
} from "@/apis/hooks";
import {
  useMovieAction,
  useMovieById,
  useMovieModification,
} from "@/apis/hooks/movies";
import { ContentHeader, LoadingIndicator } from "@/components";
import ItemOverview from "@/components/ItemOverview";
import {
  ItemEditorModal,
  MovieHistoryModal,
  MovieUploadModal,
  SubtitleToolModal,
} from "@/components/modals";
import { MovieSearchModal } from "@/components/modals/ManualSearchModal";
import { useModalControl } from "@/modules/modals";
import { createAndDispatchTask } from "@/modules/task/utilities";
import { useLanguageProfileBy } from "@/utilities/languages";
import {
  faCloudUploadAlt,
  faHistory,
  faSearch,
  faSync,
  faToolbox,
  faUser,
  faWrench,
} from "@fortawesome/free-solid-svg-icons";
import { FunctionComponent, useCallback } from "react";
import { Alert, Container, Row } from "react-bootstrap";
import { Helmet } from "react-helmet";
import { Navigate, useParams } from "react-router-dom";
import Table from "./table";

const MovieDetailView: FunctionComponent = () => {
  const param = useParams();
  const id = Number.parseInt(param.id ?? "");
  const { data: movie, isFetched } = useMovieById(id);

  const profile = useLanguageProfileBy(movie?.profileId);

  const { show } = useModalControl();

  const mutation = useMovieModification();
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
        original_format,
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
          original_format,
        },
      });
    },
    [downloadAsync]
  );

  const hasTask = useIsMovieActionRunning();

  if (isNaN(id) || (isFetched && !movie)) {
    return <Navigate to="/not-found"></Navigate>;
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
              createAndDispatchTask(movie.title, "scan-disk", action, {
                action: "scan-disk",
                radarrid: id,
              });
            }}
          >
            Scan Disk
          </ContentHeader.Button>
          <ContentHeader.Button
            icon={faSearch}
            disabled={movie.profileId === null}
            onClick={() => {
              createAndDispatchTask(movie.title, "search-subtitles", action, {
                action: "search-missing",
                radarrid: id,
              });
            }}
          >
            Search
          </ContentHeader.Button>
          <ContentHeader.Button
            icon={faUser}
            disabled={movie.profileId === null || hasTask}
            onClick={() => show(MovieSearchModal, movie)}
          >
            Manual
          </ContentHeader.Button>
          <ContentHeader.Button
            icon={faHistory}
            onClick={() => show(MovieHistoryModal, movie)}
          >
            History
          </ContentHeader.Button>
          <ContentHeader.Button
            icon={faToolbox}
            disabled={hasTask}
            onClick={() => show(SubtitleToolModal, [movie])}
          >
            Tools
          </ContentHeader.Button>
        </ContentHeader.Group>

        <ContentHeader.Group pos="end">
          <ContentHeader.Button
            disabled={!allowEdit || movie.profileId === null || hasTask}
            icon={faCloudUploadAlt}
            onClick={() => show(MovieUploadModal, movie)}
          >
            Upload
          </ContentHeader.Button>
          <ContentHeader.Button
            icon={faWrench}
            disabled={hasTask}
            onClick={() => show(ItemEditorModal, movie)}
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
      <ItemEditorModal mutation={mutation}></ItemEditorModal>
      <SubtitleToolModal></SubtitleToolModal>
      <MovieHistoryModal></MovieHistoryModal>
      <MovieUploadModal></MovieUploadModal>
      <MovieSearchModal
        download={download}
        query={useMoviesProvider}
      ></MovieSearchModal>
    </Container>
  );
};

export default MovieDetailView;
