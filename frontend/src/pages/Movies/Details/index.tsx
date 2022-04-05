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
import ItemEditForm from "@/components/forms/ItemEditForm";
import ItemOverview from "@/components/ItemOverview";
import { MovieHistoryModal, MovieUploadModal } from "@/components/modals";
import { MovieSearchModal } from "@/components/modals/ManualSearchModal";
import SubtitleTools, {
  SubtitleToolModal,
} from "@/components/modals/subtitle-tools";
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
import { Container, Popover, Stack } from "@mantine/core";
import { FunctionComponent, useCallback, useState } from "react";
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

  const [isEditing, setIsEditing] = useState(false);

  if (isNaN(id) || (isFetched && !movie)) {
    return <Navigate to="/not-found"></Navigate>;
  }

  if (!movie) {
    return <LoadingIndicator></LoadingIndicator>;
  }

  const allowEdit = movie.profileId !== undefined;

  return (
    <Container fluid px={0}>
      <Helmet>
        <title>{movie.title} - Bazarr (Movies)</title>
      </Helmet>
      <ContentHeader>
        <div>
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
        </div>
        <div>
          <ContentHeader.Button
            disabled={!allowEdit || movie.profileId === null || hasTask}
            icon={faCloudUploadAlt}
            onClick={() => show(MovieUploadModal, movie)}
          >
            Upload
          </ContentHeader.Button>
          <Popover
            opened={isEditing}
            onClose={() => setIsEditing(false)}
            placement="end"
            title="Edit Movie"
            transition="scale"
            target={
              <ContentHeader.Button
                icon={faWrench}
                disabled={hasTask}
                onClick={() => setIsEditing(true)}
              >
                Edit Movie
              </ContentHeader.Button>
            }
          >
            <ItemEditForm mutation={mutation} item={movie}></ItemEditForm>
          </Popover>
        </div>
      </ContentHeader>
      <Stack>
        <ItemOverview item={movie} details={[]}></ItemOverview>
        <Table movie={movie} profile={profile} disabled={hasTask}></Table>
      </Stack>
      <SubtitleTools></SubtitleTools>
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
