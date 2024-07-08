import { FunctionComponent, useMemo } from "react";
import { Link } from "react-router-dom";
import { Anchor, Container, Progress } from "@mantine/core";
import { useDocumentTitle } from "@mantine/hooks";
import { faBookmark as farBookmark } from "@fortawesome/free-regular-svg-icons";
import { faBookmark, faWrench } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { ColumnDef } from "@tanstack/react-table";
import { useSeriesModification, useSeriesPagination } from "@/apis/hooks";
import { Action } from "@/components";
import LanguageProfileName from "@/components/bazarr/LanguageProfile";
import { ItemEditModal } from "@/components/forms/ItemEditForm";
import { useModals } from "@/modules/modals";
import ItemView from "@/pages/views/ItemView";

const SeriesView: FunctionComponent = () => {
  const mutation = useSeriesModification();

  const query = useSeriesPagination();

  const modals = useModals();

  const columns = useMemo<ColumnDef<Item.Series>[]>(
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
        cell: ({ row: { original } }) => {
          const target = `/series/${original.sonarrSeriesId}`;
          return (
            <Anchor className="table-primary" component={Link} to={target}>
              {original.title}
            </Anchor>
          );
        },
      },
      {
        header: "Languages Profile",
        accessorKey: "profileId",
        cell: ({ row: { original } }) => {
          return (
            <LanguageProfileName
              index={original.profileId}
              empty=""
            ></LanguageProfileName>
          );
        },
      },
      {
        header: "Episodes",
        accessorKey: "episodeFileCount",
        cell: (row) => {
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
            <Progress.Root key={title} size="xl">
              <Progress.Section
                value={progress}
                color={episodeMissingCount === 0 ? "brand" : "yellow"}
              >
                <Progress.Label>{label}</Progress.Label>
              </Progress.Section>
            </Progress.Root>
          );
        },
      },
      {
        id: "sonarrSeriesId",
        cell: ({ row: { original } }) => {
          return (
            <Action
              label="Edit Series"
              tooltip={{ position: "left" }}
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
    [mutation, modals],
  );

  useDocumentTitle("Series - Bazarr");

  return (
    <Container px={0} fluid>
      <ItemView query={query} columns={columns}></ItemView>
    </Container>
  );
};

export default SeriesView;
