import { FunctionComponent, useCallback, useMemo } from "react";
import { Link } from "react-router";
import { Anchor, Badge, Container, Tooltip } from "@mantine/core";
import { useDocumentTitle } from "@mantine/hooks";
import { faBookmark as farBookmark } from "@fortawesome/free-regular-svg-icons";
import { faBookmark, faWrench } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { uniqueId } from "lodash";
import {
  moviesPaginationKey,
  moviesPaginationQuery,
  useMovieModification,
  useMovieTags,
} from "@/apis/hooks";
import { useInstanceName } from "@/apis/hooks/site";
import { Action } from "@/components";
import { AudioList } from "@/components/bazarr";
import Language from "@/components/bazarr/Language";
import LanguageProfileName from "@/components/bazarr/LanguageProfile";
import { ItemEditModal } from "@/components/forms/ItemEditForm";
import { AppColumnDef as ColumnDef } from "@/components/tables/features";
import { useModals } from "@/modules/modals";
import ItemView from "@/pages/views/ItemView";
import { BuildKey } from "@/utilities";
import { moviesViewModeKey } from "@/utilities/viewMode";
import MoviePosterCard from "./PosterCard";

const moviesFilterConfig = {
  sortFields: [
    { value: "title", label: "Name" },
    { value: "profileId", label: "Profile" },
    { value: "audioLanguage", label: "Audio" },
    { value: "createdAtTimestamp", label: "Added" },
  ],
  filters: {
    monitored: true,
    missing: true,
    profile: true,
    audio: true,
    tags: true,
  },
};

const MovieView: FunctionComponent = () => {
  const modifyMovie = useMovieModification();

  const modals = useModals();

  const columns = useMemo<ColumnDef<Item.Movie>[]>(
    () => [
      {
        id: "monitored",
        cell: ({
          row: {
            original: { monitored },
          },
        }) => (
          <Tooltip
            label={monitored ? "Monitored in Radarr" : "Unmonitored in Radarr"}
          >
            <FontAwesomeIcon icon={monitored ? faBookmark : farBookmark} />
          </Tooltip>
        ),
      },
      {
        header: "Name",
        accessorKey: "title",
        cell: ({
          row: {
            original: { title, radarrId },
          },
        }) => {
          const target = `/movies/${radarrId}`;
          return (
            <Anchor className="table-primary" component={Link} to={target}>
              {title}
            </Anchor>
          );
        },
      },
      {
        header: "Audio",
        accessorKey: "audioLanguage",
        cell: ({
          row: {
            original: { audioLanguage },
          },
        }) => {
          return <AudioList audios={audioLanguage}></AudioList>;
        },
      },
      {
        header: "Languages Profile",
        accessorKey: "profileId",
        cell: ({
          row: {
            original: { profileId },
          },
        }) => {
          return (
            <LanguageProfileName
              index={profileId}
              empty=""
            ></LanguageProfileName>
          );
        },
      },
      {
        header: "Missing Subtitles",
        accessorKey: "missingSubtitles",
        cell: ({
          row: {
            original: { missingSubtitles },
          },
        }) => {
          return (
            <>
              {missingSubtitles.map((v) => (
                <Badge
                  mr="xs"
                  color="warning"
                  key={uniqueId(`${BuildKey(v.code2, v.hi, v.forced)}_`)}
                >
                  <Language.Text value={v}></Language.Text>
                </Badge>
              ))}
            </>
          );
        },
      },
      {
        header: "Added",
        accessorKey: "createdAtTimestamp",
        cell: ({ row: { original } }) => (
          <>
            {original.createdAtTimestamp
              ? new Date(original.createdAtTimestamp).toLocaleDateString()
              : ""}
          </>
        ),
      },
      {
        id: "radarrId",
        cell: ({ row }) => {
          return (
            <Action
              label="Edit Movie"
              tooltip={{ position: "left" }}
              onClick={() =>
                modals.openContextModal(
                  ItemEditModal,
                  {
                    mutation: modifyMovie,
                    item: row.original,
                  },
                  {
                    title: row.original.title,
                  },
                )
              }
              icon={faWrench}
            ></Action>
          );
        },
      },
    ],
    [modals, modifyMovie],
  );

  const renderPoster = useCallback(
    (item: Item.Movie) => (
      <MoviePosterCard
        key={item.radarrId}
        item={item}
        onEdit={() =>
          modals.openContextModal(
            ItemEditModal,
            {
              mutation: modifyMovie,
              item,
            },
            {
              title: item.title,
            },
          )
        }
      ></MoviePosterCard>
    ),
    [modals, modifyMovie],
  );

  useDocumentTitle(`Movies - ${useInstanceName()}`);

  return (
    <Container fluid px={0}>
      <ItemView
        queryKey={moviesPaginationKey}
        queryFn={moviesPaginationQuery}
        columns={columns}
        viewModeKey={moviesViewModeKey}
        renderPoster={renderPoster}
        filterConfig={moviesFilterConfig}
        useTags={useMovieTags}
        statePrefix="movies"
      ></ItemView>
    </Container>
  );
};

export default MovieView;
