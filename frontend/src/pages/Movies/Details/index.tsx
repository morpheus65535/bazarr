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
import { Toolbox } from "@/components";
import { QueryOverlay } from "@/components/async";
import { ItemEditModal } from "@/components/forms/ItemEditForm";
import { SubtitleUploadModal } from "@/components/forms/SubtitleUploadForm";
import File, { FileOverlay } from "@/components/inputs/File";
import ItemOverview from "@/components/ItemOverview";
import { MovieHistoryModal, SubtitleToolsModal } from "@/components/modals";
import { MovieSearchModal } from "@/components/modals/ManualSearchModal";
import { useModals } from "@/modules/modals";
import { createAndDispatchTask } from "@/modules/task";
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
import { Container, Group, Stack } from "@mantine/core";
import { isNumber } from "lodash";
import { FunctionComponent, useCallback, useRef } from "react";
import { Helmet } from "react-helmet";
import { Navigate, useParams } from "react-router-dom";
import Table from "./table";

const MovieDetailView: FunctionComponent = () => {
  const param = useParams();
  const id = Number.parseInt(param.id ?? "");
  const movieQuery = useMovieById(id);
  const { data: movie, isFetched } = movieQuery;

  const profile = useLanguageProfileBy(movie?.profileId);

  const modals = useModals();

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

  const dialogRef = useRef<VoidFunction>(null);
  const onDrop = useCallback(
    (files: File[]) => {
      if (profile) {
        modals.openContextModal(SubtitleUploadModal, {
          files,
          profile,
          onComplete: (files) => {
            //
          },
        });
      }
    },
    [modals, profile]
  );

  const hasTask = useIsMovieActionRunning();

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
        <FileOverlay
          disabled={profile === undefined}
          accept={[""]}
          onDrop={onDrop}
        ></FileOverlay>
        <div hidden>
          {/* A workaround to allow click to upload files */}
          <File
            disabled={profile === undefined}
            accept={[""]}
            openRef={dialogRef}
            onDrop={onDrop}
          ></File>
        </div>
        <Toolbox>
          <Group spacing="xs">
            <Toolbox.Button
              icon={faSync}
              disabled={hasTask}
              onClick={() => {
                if (movie) {
                  createAndDispatchTask(
                    movie.title,
                    "Scanning disk...",
                    action,
                    {
                      action: "scan-disk",
                      radarrid: id,
                    }
                  );
                }
              }}
            >
              Scan Disk
            </Toolbox.Button>
            <Toolbox.Button
              icon={faSearch}
              disabled={!isNumber(movie?.profileId)}
              onClick={() => {
                if (movie) {
                  createAndDispatchTask(
                    movie.title,
                    "Searching subtitles...",
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
            </Toolbox.Button>
            <Toolbox.Button
              icon={faUser}
              disabled={!isNumber(movie?.profileId) || hasTask}
              onClick={() => {
                if (movie) {
                  modals.openContextModal(MovieSearchModal, {
                    item: movie,
                    download,
                    query: useMoviesProvider,
                  });
                }
              }}
            >
              Manual
            </Toolbox.Button>
            <Toolbox.Button
              icon={faHistory}
              onClick={() => {
                if (movie) {
                  modals.openContextModal(MovieHistoryModal, { movie });
                }
              }}
            >
              History
            </Toolbox.Button>
            <Toolbox.Button
              icon={faToolbox}
              disabled={hasTask}
              onClick={() => {
                if (movie) {
                  modals.openContextModal(SubtitleToolsModal, {
                    payload: [movie],
                  });
                }
              }}
            >
              Tools
            </Toolbox.Button>
          </Group>
          <Group spacing="xs">
            <Toolbox.Button
              disabled={!allowEdit || movie.profileId === null || hasTask}
              icon={faCloudUploadAlt}
              onClick={() => {
                dialogRef.current?.();
                // if (movie) {
                //   modals.openContextModal(MovieUploadModal, { payload: movie });
                // }
              }}
            >
              Upload
            </Toolbox.Button>
            <Toolbox.Button
              icon={faWrench}
              disabled={hasTask}
              onClick={() => {
                if (movie) {
                  modals.openContextModal(ItemEditModal, {
                    item: movie,
                    mutation,
                  });
                }
              }}
            >
              Edit Movie
            </Toolbox.Button>
          </Group>
        </Toolbox>
        <Stack>
          <ItemOverview item={movie ?? null} details={[]}></ItemOverview>
          <Table
            movie={movie ?? null}
            profile={profile}
            disabled={hasTask}
          ></Table>
        </Stack>
      </QueryOverlay>
    </Container>
  );
};

export default MovieDetailView;
