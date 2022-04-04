import { useSeriesModification, useSeriesPagination } from "@/apis/hooks";
import LanguageProfileName from "@/components/bazarr/LanguageProfile";
import { ItemEditorModal } from "@/components/modals";
import ItemView from "@/components/views/ItemView";
import { useModalControl } from "@/modules/modals";
import { BuildKey } from "@/utilities";
import { faWrench } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import {
  ActionIcon,
  Anchor,
  Badge,
  Container,
  Progress,
  Text,
} from "@mantine/core";
import { FunctionComponent, useMemo } from "react";
import { Helmet } from "react-helmet";
import { Link } from "react-router-dom";
import { Column } from "react-table";

const SeriesView: FunctionComponent = () => {
  const mutation = useSeriesModification();

  const query = useSeriesPagination();

  const columns: Column<Item.Series>[] = useMemo<Column<Item.Series>[]>(
    () => [
      {
        Header: "Name",
        accessor: "title",
        className: "text-nowrap",
        Cell: ({ row, value }) => {
          const target = `/series/${row.original.sonarrSeriesId}`;
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
            <Badge
              color="secondary"
              className="mr-2"
              key={BuildKey(v.code2, v.forced, v.hi)}
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
          return (
            <LanguageProfileName index={value} empty=""></LanguageProfileName>
          );
        },
      },
      {
        Header: "Episodes",
        accessor: "episodeFileCount",
        Cell: (row) => {
          const { episodeFileCount, episodeMissingCount, profileId, title } =
            row.row.original;
          let progress = 0;
          let label = "";
          if (episodeFileCount === 0 || !profileId) {
            progress = 0.0;
          } else {
            progress = (1.0 - episodeMissingCount / episodeFileCount) * 100.0;
            label = `${
              episodeFileCount - episodeMissingCount
            }/${episodeFileCount}`;
          }

          return (
            <Progress
              key={title}
              size="xl"
              color={episodeMissingCount === 0 ? "blue" : "yellow"}
              value={progress}
              label={label}
            ></Progress>
          );
        },
      },
      {
        accessor: "sonarrSeriesId",
        Cell: ({ row: { original } }) => {
          const { show } = useModalControl();
          return (
            <ActionIcon
              variant="light"
              onClick={() => show(ItemEditorModal, original)}
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
    <Container px={0} fluid>
      <Helmet>
        <title>Series - Bazarr</title>
      </Helmet>
      <ItemView query={query} columns={columns}></ItemView>
      <ItemEditorModal mutation={mutation}></ItemEditorModal>
    </Container>
  );
};

export default SeriesView;
