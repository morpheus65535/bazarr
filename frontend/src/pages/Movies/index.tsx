import { useMovieModification, useMoviesPagination } from "@/apis/hooks";
import { Action } from "@/components";
import { AudioList } from "@/components/bazarr";
import Language from "@/components/bazarr/Language";
import LanguageProfileName from "@/components/bazarr/LanguageProfile";
import { ItemEditModal } from "@/components/forms/ItemEditForm";
import { useModals } from "@/modules/modals";
import ItemView from "@/pages/views/ItemView";
import { useTableStyles } from "@/styles";
import { BuildKey } from "@/utilities";
import { faBookmark as farBookmark } from "@fortawesome/free-regular-svg-icons";
import { faBookmark, faWrench } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { Anchor, Badge, Container } from "@mantine/core";
import { useDocumentTitle } from "@mantine/hooks";
import { FunctionComponent, useMemo } from "react";
import { Link } from "react-router-dom";
import { Column } from "react-table";

const MovieView: FunctionComponent = () => {
  const query = useMoviesPagination();

  const columns: Column<Item.Movie>[] = useMemo<Column<Item.Movie>[]>(
    () => [
      {
        accessor: "monitored",
        Cell: ({ value }) => (
          <FontAwesomeIcon
            title={value ? "monitored" : "unmonitored"}
            icon={value ? faBookmark : farBookmark}
          ></FontAwesomeIcon>
        ),
      },
      {
        Header: "Name",
        accessor: "title",
        Cell: ({ row, value }) => {
          const { classes } = useTableStyles();
          const target = `/movies/${row.original.radarrId}`;
          return (
            <Anchor className={classes.primary} component={Link} to={target}>
              {value}
            </Anchor>
          );
        },
      },
      {
        Header: "Audio",
        accessor: "audio_language",
        Cell: ({ value }) => {
          return <AudioList audios={value}></AudioList>;
        },
      },
      {
        Header: "Languages Profile",
        accessor: "profileId",
        Cell: ({ value }) => {
          return (
            <LanguageProfileName index={value} empty=""></LanguageProfileName>
          );
        },
      },
      {
        Header: "Missing Subtitles",
        accessor: "missing_subtitles",
        Cell: (row) => {
          const missing = row.value;
          return missing.map((v) => (
            <Badge
              mr="xs"
              color="yellow"
              key={BuildKey(v.code2, v.hi, v.forced)}
            >
              <Language.Text value={v}></Language.Text>
            </Badge>
          ));
        },
      },
      {
        accessor: "radarrId",
        Cell: ({ row }) => {
          const modals = useModals();
          const mutation = useMovieModification();
          return (
            <Action
              label="Edit Movie"
              tooltip={{ position: "left" }}
              variant="light"
              onClick={() =>
                modals.openContextModal(
                  ItemEditModal,
                  {
                    mutation,
                    item: row.original,
                  },
                  {
                    title: row.original.title,
                  }
                )
              }
              icon={faWrench}
            ></Action>
          );
        },
      },
    ],
    []
  );

  useDocumentTitle("Movies - Bazarr");

  return (
    <Container fluid px={0}>
      <ItemView query={query} columns={columns}></ItemView>
    </Container>
  );
};

export default MovieView;
