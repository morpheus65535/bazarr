import { useMovieModification, useMoviesPagination } from "@/apis/hooks";
import { ActionBadge, TextPopover } from "@/components";
import Language from "@/components/bazarr/Language";
import LanguageProfile from "@/components/bazarr/LanguageProfile";
import { ItemEditorModal } from "@/components/modals";
import ItemView from "@/components/views/ItemView";
import { useModalControl } from "@/modules/modals";
import { BuildKey } from "@/utilities";
import { faBookmark as farBookmark } from "@fortawesome/free-regular-svg-icons";
import { faBookmark, faWrench } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { Badge, Container } from "@mantine/core";
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
            <TextPopover text={row.original.sceneName} delay={1}>
              <Link to={target}>
                <span>{value}</span>
              </Link>
            </TextPopover>
          );
        },
      },
      {
        Header: "Audio",
        accessor: "audio_language",
        Cell: (row) => {
          return row.value.map((v) => (
            <Badge
              color="secondary"
              className="mr-2"
              key={BuildKey(v.code2, v.code2, v.hi)}
            >
              {v.name}
            </Badge>
          ));
        },
      },
      {
        Header: "Languages Profile",
        accessor: "profileId",
        Cell: ({ value }) => {
          return <LanguageProfile index={value} empty=""></LanguageProfile>;
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
            <ActionBadge
              icon={faWrench}
              onClick={() => show(ItemEditorModal, row.original)}
            ></ActionBadge>
          );
        },
      },
    ],
    []
  );

  return (
    <Container fluid>
      <Helmet>
        <title>Movies - Bazarr</title>
      </Helmet>
      <ItemView query={query} columns={columns}></ItemView>
      <ItemEditorModal mutation={mutation}></ItemEditorModal>
    </Container>
  );
};

export default MovieView;
