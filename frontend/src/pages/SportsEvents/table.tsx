import React, { forwardRef, useEffect, useMemo } from "react";
import { Group, Text, Tooltip } from "@mantine/core";
import { faBookmark as farBookmark } from "@fortawesome/free-regular-svg-icons";
import { faBookmark, faHistory } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { useShowOnlyDesired } from "@/apis/hooks/site";
import { Action, GroupTable } from "@/components";
import { AudioList } from "@/components/bazarr";
import { SportsEventHistoryModal } from "@/components/modals";
import {
  AppColumnDef as ColumnDef,
  AppTable as TableInstance,
} from "@/components/tables/features";
import TextPopover from "@/components/TextPopover";
import { useModals } from "@/modules/modals";
import { BuildKey, filterSubtitleBy } from "@/utilities";
import { useProfileItemsToLanguages } from "@/utilities/languages";
import { SportsSubtitle } from "./components";

interface Props {
  events: Item.SportsEvent[] | null;
  disabled?: boolean;
  profile?: Language.Profile;
  onAllRowsExpandedChanged: (isAllRowsExpanded: boolean) => void;
}

const Table = forwardRef<TableInstance<Item.SportsEvent> | null, Props>(
  ({ events, profile, disabled, onAllRowsExpandedChanged }, ref) => {
    const onlyDesired = useShowOnlyDesired();

    const tableRef =
      ref as React.MutableRefObject<TableInstance<Item.SportsEvent> | null>;

    const profileItems = useProfileItemsToLanguages(profile);

    const modals = useModals();

    const SubtitlesCell = React.memo(
      ({ event }: { event: Item.SportsEvent }) => {
        const leagueId = event.sportarrLeagueId;

        const elements = useMemo(() => {
          const eventId = event.sportsEventId;

          const missing = event.missingSubtitles.map((val, idx) => (
            <SportsSubtitle
              missing
              key={BuildKey(idx, val.code2, "missing")}
              leagueId={leagueId}
              eventId={eventId}
              subtitle={val}
            ></SportsSubtitle>
          ));

          const rawSubtitles = onlyDesired
            ? filterSubtitleBy(event.subtitles, profileItems)
            : event.subtitles;

          const subtitles = rawSubtitles.map((val, idx) => (
            <SportsSubtitle
              key={BuildKey(idx, val.code2, "valid")}
              leagueId={leagueId}
              eventId={eventId}
              subtitle={val}
            ></SportsSubtitle>
          ));

          return [...missing, ...subtitles];
        }, [event, leagueId]);

        return (
          <Group gap="xs" wrap="nowrap">
            {elements}
          </Group>
        );
      },
    );

    const columns = useMemo<ColumnDef<Item.SportsEvent>[]>(
      () => [
        {
          id: "monitored",
          cell: ({
            row: {
              original: { monitored },
            },
          }) => {
            return (
              <Tooltip
                label={
                  monitored
                    ? "Monitored in Sportarr"
                    : "Unmonitored in Sportarr"
                }
              >
                <FontAwesomeIcon icon={monitored ? faBookmark : farBookmark} />
              </Tooltip>
            );
          },
        },
        {
          header: "",
          accessorKey: "season",
          cell: ({
            row: {
              original: { season },
            },
          }) => {
            return <Text span>Season {season}</Text>;
          },
        },
        {
          header: "Event",
          accessorKey: "episode",
        },
        {
          header: "Title",
          accessorKey: "title",
          cell: ({
            row: {
              original: { sceneName, title, partName },
            },
          }) => {
            // Most events are a single file. A multi part event names each
            // file, an undercard and a main card for example.
            const label = partName ? `${title} - ${partName}` : title;

            return (
              <TextPopover text={sceneName}>
                <Text className="table-primary">{label}</Text>
              </TextPopover>
            );
          },
        },
        {
          header: "Date",
          accessorKey: "broadcastDate",
          cell: ({
            row: {
              original: { broadcastDate },
            },
          }) => {
            return <Text className="table-no-wrap">{broadcastDate ?? ""}</Text>;
          },
        },
        {
          header: "Audio",
          accessorKey: "audioLanguage",
          cell: ({
            row: {
              original: { audioLanguage },
            },
          }) => <AudioList audios={audioLanguage}></AudioList>,
        },
        {
          header: "Subtitles",
          accessorKey: "missingSubtitles",
          cell: ({ row: { original } }) => {
            return <SubtitlesCell event={original} />;
          },
        },
        {
          header: "Actions",
          cell: ({ row }) => {
            return (
              <Group gap="xs" wrap="nowrap">
                <Action
                  label="History"
                  disabled={disabled}
                  onClick={() => {
                    modals.openContextModal(
                      SportsEventHistoryModal,
                      {
                        event: row.original,
                      },
                      {
                        title: `History - ${row.original.title}`,
                      },
                    );
                  }}
                  icon={faHistory}
                ></Action>
              </Group>
            );
          },
        },
      ],
      [disabled, modals, SubtitlesCell],
    );

    const maxSeason = useMemo(
      () =>
        events?.reduce<number>(
          (prev, curr) => Math.max(prev, curr.season),
          0,
        ) ?? 0,
      [events],
    );

    useEffect(() => {
      tableRef?.current?.setExpanded(() => ({ [`season:${maxSeason}`]: true }));
    }, [tableRef, maxSeason]);

    return (
      <GroupTable
        columns={columns}
        data={events ?? []}
        instanceRef={tableRef}
        onAllRowsExpandedChanged={onAllRowsExpandedChanged}
        initialState={{
          sorting: [
            { id: "season", desc: true },
            { id: "episode", desc: true },
          ],
          grouping: ["season"],
        }}
        tableStyles={{ emptyText: "No Event Found For This League" }}
      ></GroupTable>
    );
  },
);

export default Table;
