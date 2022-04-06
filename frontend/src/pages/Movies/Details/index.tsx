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
import { ContentHeader } from "@/components";
import { QueryOverlay } from "@/components/async";
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
import { Container, Group, Popover, Stack } from "@mantine/core";
import { isNumber } from "lodash";
import { FunctionComponent, useCallback, useState } from "react";
import { Helmet } from "react-helmet";
import { Navigate, useParams } from "react-router-dom";
import Table from "./table";

const MovieDetailView: FunctionComponent = () => {
  const param = useParams();
  const id = Number.parseInt(param.id ?? "");
  const movieQuery = useMovieById(id);
  const { data: movie, isFetched } = movieQuery;

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

  const allowEdit = movie?.profileId !== undefined;

  return (
    <Container fluid px={0}>
      <QueryOverlay result={movieQuery}>
        <Helmet>
          <title>{movie?.title ?? "Unknown Movie"} - Bazarr (Movies)</title>
        </Helmet>
        <ContentHeader>
          <Group spacing="xs">
            <ContentHeader.Button
              icon={faSync}
              disabled={hasTask}
              onClick={() => {
                if (movie) {
                  createAndDispatchTask(movie.title, "scan-disk", action, {
                    action: "scan-disk",
                    radarrid: id,
                  });
                }
              }}
            >
              Scan Disk
            </ContentHeader.Button>
            <ContentHeader.Button
              icon={faSearch}
              disabled={!isNumber(movie?.profileId)}
              onClick={() => {
                if (movie) {
                  createAndDispatchTask(
                    movie.title,
                    "search-subtitles",
                    action,
                    {
                      action: "search-missing",
                      radarrid: id,
                    }
                  );
                }
              }}
            >
              Search
            </ContentHeader.Button>
            <ContentHeader.Button
              icon={faUser}
              disabled={!isNumber(movie?.profileId) || hasTask}
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
          </Group>
          <Group spacing="xs">
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
              <ItemEditForm
                mutation={mutation}
                item={movie ?? null}
                onCancel={() => setIsEditing(false)}
                onComplete={() => setIsEditing(false)}
              ></ItemEditForm>
            </Popover>
          </Group>
        </ContentHeader>
        <Stack>
          <ItemOverview item={movie ?? null} details={[]}></ItemOverview>
          <Table
            movie={movie ?? null}
            profile={profile}
            disabled={hasTask}
          ></Table>
        </Stack>
        <SubtitleTools></SubtitleTools>
        <MovieHistoryModal></MovieHistoryModal>
        <MovieUploadModal></MovieUploadModal>
        <MovieSearchModal
          download={download}
          query={useMoviesProvider}
        ></MovieSearchModal>
      </QueryOverlay>
    </Container>
  );
};

export default MovieDetailView;
