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
import { Action, DropOverlay, Toolbox } from "@/components";
import { QueryOverlay } from "@/components/async";
import { ItemEditModal } from "@/components/forms/ItemEditForm";
import { MovieUploadModal } from "@/components/forms/MovieUploadForm";
import { MovieHistoryModal, SubtitleToolsModal } from "@/components/modals";
import { MovieSearchModal } from "@/components/modals/ManualSearchModal";
import { useModals } from "@/modules/modals";
import { notification, task, TaskGroup } from "@/modules/task";
import ItemOverview from "@/pages/views/ItemOverview";
import { useLanguageProfileBy } from "@/utilities/languages";
import {
  faCloudUploadAlt,
  faEllipsis,
  faHistory,
  faSearch,
  faSync,
  faToolbox,
  faUser,
  faWrench,
} from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { Container, Group, Menu, Stack } from "@mantine/core";
import { useDocumentTitle } from "@mantine/hooks";
import { showNotification } from "@mantine/notifications";
import { isNumber } from "lodash";
import { FunctionComponent, useCallback } from "react";
import { FileRejection, useDropzone } from "react-dropzone";
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

  const onDrop = useCallback(
    (files: File[], rejections: FileRejection[]) => {
      if (movie && profile) {
        if (rejections.length > 0) {
          showNotification(
            notification.warn(
              "Some files are rejected",
              `${rejections.length} files are invalid`
            )
          );
        }
        modals.openContextModal(MovieUploadModal, {
          files,
          movie,
        });
      } else {
        showNotification(
          notification.warn(
            "Cannot Upload Files",
            "movie or language profile is not ready"
          )
        );
      }
    },
    [modals, movie, profile]
  );

  const hasTask = useIsMovieActionRunning();

  useDocumentTitle(`${movie?.title ?? "Unknown Movie"} - Bazarr (Movies)`);

  const dropzone = useDropzone({
    disabled: profile === undefined,
    onDrop,
    noClick: true,
  });

  if (isNaN(id) || (isFetched && !movie)) {
    return <Navigate to="/not-found"></Navigate>;
  }

  const allowEdit = movie?.profileId !== undefined;

  return (
    <Container fluid px={0}>
      <QueryOverlay result={movieQuery}>
        <DropOverlay state={dropzone}>
          {/* <FileOverlay
          disabled={profile === undefined}
          accept={[""]}
          onDrop={onDrop}
        ></FileOverlay> */}
          {/* <div hidden>
          <File
            disabled={profile === undefined}
            accept={[""]}
            openRef={dialogRef}
            onDrop={onDrop}
          ></File>
        </div> */}
          <Toolbox>
            <Group spacing="xs">
              <Toolbox.Button
                icon={faSync}
                disabled={hasTask}
                onClick={() => {
                  if (movie) {
                    task.create(movie.title, TaskGroup.ScanDisk, action, {
                      action: "scan-disk",
                      radarrid: id,
                    });
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
                    task.create(movie.title, TaskGroup.SearchSubtitle, action, {
                      action: "search-missing",
                      radarrid: id,
                    });
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
            </Group>
            <Group spacing="xs">
              <Toolbox.Button
                disabled={!allowEdit || movie.profileId === null || hasTask}
                icon={faCloudUploadAlt}
                onClick={dropzone.open}
              >
                Upload
              </Toolbox.Button>
              <Toolbox.Button
                icon={faWrench}
                disabled={hasTask}
                onClick={() => {
                  if (movie) {
                    modals.openContextModal(
                      ItemEditModal,
                      {
                        item: movie,
                        mutation,
                      },
                      { title: movie.title }
                    );
                  }
                }}
              >
                Edit Movie
              </Toolbox.Button>
              <Menu
                control={
                  <Action
                    label="More Actions"
                    icon={faEllipsis}
                    disabled={hasTask}
                  />
                }
              >
                <Menu.Item
                  icon={<FontAwesomeIcon icon={faToolbox} />}
                  onClick={() => {
                    if (movie) {
                      modals.openContextModal(SubtitleToolsModal, {
                        payload: [movie],
                      });
                    }
                  }}
                >
                  Mass Edit
                </Menu.Item>
                <Menu.Item
                  icon={<FontAwesomeIcon icon={faHistory} />}
                  onClick={() => {
                    if (movie) {
                      modals.openContextModal(MovieHistoryModal, { movie });
                    }
                  }}
                >
                  History
                </Menu.Item>
              </Menu>
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
        </DropOverlay>
      </QueryOverlay>
    </Container>
  );
};

export default MovieDetailView;
