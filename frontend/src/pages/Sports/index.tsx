import { FunctionComponent, useMemo } from "react";
import { Container, Group, Progress } from "@mantine/core";
import { useDocumentTitle } from "@mantine/hooks";
import { faBookmark as farBookmark } from "@fortawesome/free-regular-svg-icons";
import { faBookmark, faWrench } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import {
  sportsLeaguesPaginationKey,
  sportsLeaguesPaginationQuery,
  useSportsLeagueModification,
  useSportsLeagues,
  useSportsLeagueTags,
} from "@/apis/hooks";
import { useInstanceName } from "@/apis/hooks/site";
import { Action } from "@/components";
import { AudioList } from "@/components/bazarr";
import LanguageProfileName from "@/components/bazarr/LanguageProfile";
import { ItemEditModal } from "@/components/forms/ItemEditForm";
import { AppColumnDef as ColumnDef } from "@/components/tables/features";
import { useModals } from "@/modules/modals";
import ItemView from "@/pages/views/ItemView";

const sportsFilterConfig = {
  sortFields: [
    { value: "title", label: "Name" },
    { value: "sport", label: "Sport" },
    { value: "episodeFileCount", label: "Files" },
    { value: "episodeMissingCount", label: "Missing" },
    { value: "profileId", label: "Profile" },
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

const SportsView: FunctionComponent = () => {
  const mutation = useSportsLeagueModification();

  const modals = useModals();

  const columns = useMemo<ColumnDef<Item.SportsLeague>[]>(
    () => [
      {
        id: "status",
        cell: ({ row: { original } }) => (
          <Group gap="xs" wrap="nowrap">
            <FontAwesomeIcon
              title={original.monitored ? "monitored" : "unmonitored"}
              icon={original.monitored ? faBookmark : farBookmark}
            ></FontAwesomeIcon>
          </Group>
        ),
      },
      {
        header: "Name",
        accessorKey: "title",
      },
      {
        // Sport is the closest a league has to a series type.
        header: "Sport",
        accessorKey: "sport",
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
        // Counted per playable file, because a row is one part. An event with
        // two parts needs subtitles for both.
        header: "Files",
        accessorKey: "episodeFileCount",
        cell: (row) => {
          const { episodeFileCount, episodeMissingCount, profileId, title } =
            row.row.original;

          const label = `${episodeFileCount - episodeMissingCount}/${episodeFileCount}`;
          return (
            <Progress.Root key={title} size="xl">
              <Progress.Section
                value={
                  episodeFileCount === 0 || !profileId
                    ? 0
                    : (1.0 - episodeMissingCount / episodeFileCount) * 100.0
                }
                color={episodeMissingCount === 0 ? "brand" : "warning"}
              >
                <Progress.Label>{label}</Progress.Label>
              </Progress.Section>
              {episodeMissingCount === episodeFileCount && (
                <Progress.Label
                  styles={{
                    label: {
                      position: "absolute",
                      top: "3px",
                      left: "50%",
                      transform: "translateX(-50%)",
                    },
                  }}
                >
                  {label}
                </Progress.Label>
              )}
            </Progress.Root>
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
        id: "sportarrLeagueId",
        cell: ({ row: { original } }) => {
          return (
            <Action
              label="Edit League"
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

  useDocumentTitle(`Sports - ${useInstanceName()}`);

  return (
    <Container px={0} fluid>
      <ItemView
        queryKey={sportsLeaguesPaginationKey}
        queryFn={sportsLeaguesPaginationQuery}
        columns={columns}
        filterConfig={sportsFilterConfig}
        useTags={useSportsLeagueTags}
        statePrefix="sports"
        useAllItems={useSportsLeagues}
        modifyMutation={mutation}
      ></ItemView>
    </Container>
  );
};

export default SportsView;
