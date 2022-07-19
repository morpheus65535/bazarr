import {
  useEpisodesBySeriesId,
  useIsAnyActionRunning,
  useSeriesAction,
  useSeriesById,
  useSeriesModification,
} from "@/apis/hooks";
import { DropOverlay, Toolbox } from "@/components";
import { QueryOverlay } from "@/components/async";
import { ItemEditModal } from "@/components/forms/ItemEditForm";
import { SeriesUploadModal } from "@/components/forms/SeriesUploadForm";
import { SubtitleToolsModal } from "@/components/modals";
import { useModals } from "@/modules/modals";
import { notification, task, TaskGroup } from "@/modules/task";
import ItemOverview from "@/pages/views/ItemOverview";
import { useLanguageProfileBy } from "@/utilities/languages";
import {
  faAdjust,
  faBriefcase,
  faCloudUploadAlt,
  faHdd,
  faSearch,
  faSync,
  faWrench,
} from "@fortawesome/free-solid-svg-icons";
import { Container, Group, Stack } from "@mantine/core";
import { useDocumentTitle } from "@mantine/hooks";
import { showNotification } from "@mantine/notifications";
import { FunctionComponent, useCallback, useMemo } from "react";
import { FileRejection, useDropzone } from "react-dropzone";
import { Navigate, useParams } from "react-router-dom";
import Table from "./table";

const SeriesEpisodesView: FunctionComponent = () => {
  const params = useParams();
  const id = Number.parseInt(params.id as string);

  const seriesQuery = useSeriesById(id);
  const episodesQuery = useEpisodesBySeriesId(id);

  const { data: episodes } = episodesQuery;
  const { data: series, isFetched } = seriesQuery;

  const mutation = useSeriesModification();
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

  const modals = useModals();

  const profile = useLanguageProfileBy(series?.profileId);

  const hasTask = useIsAnyActionRunning();

  const onDrop = useCallback(
    (files: File[], rejections: FileRejection[]) => {
      if (series && profile) {
        if (rejections.length > 0) {
          showNotification(
            notification.warn(
              "Some files are rejected",
              `${rejections.length} files are invalid`
            )
          );
        }

        modals.openContextModal(SeriesUploadModal, {
          files,
          series,
        });
      } else {
        showNotification(
          notification.warn(
            "Cannot Upload Files",
            "series or language profile is not ready"
          )
        );
      }
    },
    [modals, profile, series]
  );

  const dropzone = useDropzone({
    disabled: profile === undefined,
    noClick: true,
    onDrop,
  });

  useDocumentTitle(`${series?.title ?? "Unknown Series"} - Bazarr (Series)`);

  if (isNaN(id) || (isFetched && !series)) {
    return <Navigate to="/not-found"></Navigate>;
  }

  return (
    <Container px={0} fluid>
      <QueryOverlay result={seriesQuery}>
        <DropOverlay state={dropzone}>
          <Toolbox>
            <Group spacing="xs">
              <Toolbox.Button
                icon={faSync}
                disabled={!available || hasTask}
                onClick={() => {
                  if (series) {
                    task.create(series.title, TaskGroup.ScanDisk, action, {
                      action: "scan-disk",
                      seriesid: id,
                    });
                  }
                }}
              >
                Scan Disk
              </Toolbox.Button>
              <Toolbox.Button
                icon={faSearch}
                onClick={() => {
                  if (series) {
                    task.create(
                      series.title,
                      TaskGroup.SearchSubtitle,
                      action,
                      {
                        action: "search-missing",
                        seriesid: id,
                      }
                    );
                  }
                }}
                disabled={
                  series === undefined ||
                  series.episodeFileCount === 0 ||
                  series.profileId === null ||
                  !available
                }
              >
                Search
              </Toolbox.Button>
            </Group>
            <Group spacing="xs">
              <Toolbox.Button
                disabled={
                  series === undefined ||
                  series.episodeFileCount === 0 ||
                  !available ||
                  hasTask
                }
                icon={faBriefcase}
                onClick={() => {
                  if (episodes) {
                    modals.openContextModal(SubtitleToolsModal, {
                      payload: episodes,
                    });
                  }
                }}
              >
                Mass Edit
              </Toolbox.Button>
              <Toolbox.Button
                disabled={
                  series === undefined ||
                  series.episodeFileCount === 0 ||
                  series.profileId === null ||
                  !available
                }
                icon={faCloudUploadAlt}
                onClick={dropzone.open}
              >
                Upload
              </Toolbox.Button>
              <Toolbox.Button
                icon={faWrench}
                disabled={hasTask}
                onClick={() => {
                  if (series) {
                    modals.openContextModal(
                      ItemEditModal,
                      {
                        item: series,
                        mutation,
                      },
                      { title: series.title }
                    );
                  }
                }}
              >
                Edit Series
              </Toolbox.Button>
            </Group>
          </Toolbox>
          <Stack>
            <ItemOverview
              item={series ?? null}
              details={details}
            ></ItemOverview>
            <QueryOverlay result={episodesQuery}>
              <Table
                episodes={episodes ?? null}
                profile={profile}
                disabled={hasTask || !series || series.profileId === null}
              ></Table>
            </QueryOverlay>
          </Stack>
        </DropOverlay>
      </QueryOverlay>
    </Container>
  );
};

export default SeriesEpisodesView;
