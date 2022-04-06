import { useMovieModification, useMoviesPagination } from "@/apis/hooks";
import Language from "@/components/bazarr/Language";
import LanguageProfileName from "@/components/bazarr/LanguageProfile";
import { ItemEditModal } from "@/components/modals";
import ItemView from "@/components/views/ItemView";
import { useModalControl } from "@/modules/modals";
import { BuildKey } from "@/utilities";
import { faBookmark as farBookmark } from "@fortawesome/free-regular-svg-icons";
import { faBookmark, faWrench } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { ActionIcon, Anchor, Badge, Container, Text } from "@mantine/core";
import { FunctionComponent, useMemo } from "react";
import { Helmet } from "react-helmet";
import { Link } from "react-router-dom";
import { Column } from "react-table";

const MovieView: FunctionComponent = () => {
  const mutation = useMovieModification();

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
        className: "text-nowrap",
        Cell: ({ row, value }) => {
          const target = `/movies/${row.original.radarrId}`;
          return (
            <Anchor component={Link} to={target}>
              <Text>{value}</Text>
            </Anchor>
          );
        },
      },
      {
        Header: "Audio",
        accessor: "audio_language",
        Cell: (row) => {
          return row.value.map((v) => (
            <Badge key={BuildKey(v.code2, v.code2, v.hi)}>{v.name}</Badge>
          ));
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
              className="mx-2"
              color="warning"
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
          const { show } = useModalControl();
          return (
            <ActionIcon
              variant="light"
              onClick={() => show(ItemEditModal, row.original)}
            >
              <FontAwesomeIcon icon={faWrench}></FontAwesomeIcon>
            </ActionIcon>
          );
        },
      },
    ],
    []
  );

  return (
    <Container fluid px={0}>
      <Helmet>
        <title>Movies - Bazarr</title>
      </Helmet>
      <ItemView query={query} columns={columns}></ItemView>
      <ItemEditModal mutation={mutation}></ItemEditModal>
    </Container>
  );
};

export default MovieView;
