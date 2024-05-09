import { FunctionComponent, useMemo } from "react";
import { Link } from "react-router-dom";
import { Column } from "react-table";
import { Anchor, Container, Progress } from "@mantine/core";
import { useDocumentTitle } from "@mantine/hooks";
import { useSeriesModification, useSeriesPagination } from "@/apis/hooks";
import { Action } from "@/components";
import LanguageProfileName from "@/components/bazarr/LanguageProfile";
import { ItemEditModal } from "@/components/forms/ItemEditForm";
import { useModals } from "@/modules/modals";
import ItemView from "@/pages/views/ItemView";
import { useTableStyles } from "@/styles";

import { faBookmark as farBookmark } from "@fortawesome/free-regular-svg-icons";
import { faBookmark, faWrench } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";

const SeriesView: FunctionComponent = () => {
  const mutation = useSeriesModification();

  const query = useSeriesPagination();

  const columns: Column<Item.Series>[] = useMemo<Column<Item.Series>[]>(
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
          const target = `/series/${row.original.sonarrSeriesId}`;
          return (
            <Anchor className={classes.primary} component={Link} to={target}>
              {value}
            </Anchor>
          );
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
              color={episodeMissingCount === 0 ? "brand" : "yellow"}
              value={progress}
              label={label}
            ></Progress>
          );
        },
      },
      {
        accessor: "sonarrSeriesId",
        Cell: ({ row: { original } }) => {
          const modals = useModals();
          return (
            <Action
              label="Edit Series"
              tooltip={{ position: "left" }}
              variant="light"
              onClick={() =>
                modals.openContextModal(
                  ItemEditModal,
                  {
                    mutation,
                    item: original,
                  },
                  {
                    title: original.title,
                  },
                )
              }
              icon={faWrench}
            ></Action>
          );
        },
      },
    ],
    [mutation],
  );

  useDocumentTitle("Series - Bazarr");

  return (
    <Container px={0} fluid>
      <ItemView query={query} columns={columns}></ItemView>
    </Container>
  );
};

export default SeriesView;
