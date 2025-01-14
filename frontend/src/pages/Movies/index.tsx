import { FunctionComponent, useMemo } from "react";
import { Link } from "react-router";
import { Anchor, Badge, Container } from "@mantine/core";
import { useDocumentTitle } from "@mantine/hooks";
import { faBookmark as farBookmark } from "@fortawesome/free-regular-svg-icons";
import { faBookmark, faWrench } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { ColumnDef } from "@tanstack/react-table";
import { uniqueId } from "lodash";
import { useMovieModification, useMoviesPagination } from "@/apis/hooks";
import { Action } from "@/components";
import { AudioList } from "@/components/bazarr";
import Language from "@/components/bazarr/Language";
import LanguageProfileName from "@/components/bazarr/LanguageProfile";
import { ItemEditModal } from "@/components/forms/ItemEditForm";
import { useModals } from "@/modules/modals";
import ItemView from "@/pages/views/ItemView";
import { BuildKey } from "@/utilities";

const MovieView: FunctionComponent = () => {
  const modifyMovie = useMovieModification();

  const modals = useModals();

  const query = useMoviesPagination();

  const columns = useMemo<ColumnDef<Item.Movie>[]>(
    () => [
      {
        id: "monitored",
        cell: ({
          row: {
            original: { monitored },
          },
        }) => (
          <FontAwesomeIcon
            title={monitored ? "monitored" : "unmonitored"}
            icon={monitored ? faBookmark : farBookmark}
          ></FontAwesomeIcon>
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
        accessorKey: "audio_language",
        cell: ({
          row: {
            original: { audio_language: audioLanguage },
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
        accessorKey: "missing_subtitles",
        cell: ({
          row: {
            original: { missing_subtitles: missingSubtitles },
          },
        }) => {
          return (
            <>
              {missingSubtitles.map((v) => (
                <Badge
                  mr="xs"
                  color="yellow"
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

  useDocumentTitle("Movies - Bazarr");

  return (
    <Container fluid px={0}>
      <ItemView query={query} columns={columns}></ItemView>
    </Container>
  );
};

export default MovieView;
