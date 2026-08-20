import React, { forwardRef, useCallback, useEffect, useMemo } from "react";
import { Group, Text, Tooltip } from "@mantine/core";
import { faBookmark as farBookmark } from "@fortawesome/free-regular-svg-icons";
import {
  faBookmark,
  faHistory,
  faUser,
} from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { useDownloadEpisodeSubtitles, useEpisodesProvider } from "@/apis/hooks";
import { useShowOnlyDesired } from "@/apis/hooks/site";
import { Action, GroupTable } from "@/components";
import { AudioList } from "@/components/bazarr";
import { EpisodeHistoryModal } from "@/components/modals";
import { EpisodeSearchModal } from "@/components/modals/ManualSearchModal";
import {
  AppColumnDef as ColumnDef,
  AppTable as TableInstance,
} from "@/components/tables/features";
import TextPopover from "@/components/TextPopover";
import { useModals } from "@/modules/modals";
import { BuildKey } from "@/utilities";
import { Subtitle } from "./components";

interface Props {
  episodes: Item.Episode[] | null;
  disabled?: boolean;
  profile?: Language.Profile;
  onAllRowsExpandedChanged: (isAllRowsExpanded: boolean) => void;
}

const Table = forwardRef<TableInstance<Item.Episode> | null, Props>(
  ({ episodes, disabled, onAllRowsExpandedChanged }, ref) => {
    const tableRef =
      ref as React.MutableRefObject<TableInstance<Item.Episode> | null>;

    const { mutateAsync } = useDownloadEpisodeSubtitles();

    const modals = useModals();

    const download = useCallback(
      (item: Item.Episode, result: SearchResultType) => {
        const {
          language,
          hearingImpaired: hi,
          forced,
          provider,
          subtitle,
          originalFormat,
        } = result;
        const { sonarrSeriesId: seriesId, sonarrEpisodeId: episodeId } = item;

        return mutateAsync({
          seriesId,
          episodeId,
          form: {
            language,
            hi,
            forced,
            provider,
            subtitle,
            originalFormat,
          },
        });
      },
      [mutateAsync],
    );

    const SubtitlesCell = React.memo(
      ({ episode }: { episode: Item.Episode }) => {
        const seriesId = episode.sonarrSeriesId;

        const elements = useMemo(() => {
          const episodeId = episode.sonarrEpisodeId;

          const missing = episode.missingSubtitles.map((val, idx) => (
            <Subtitle
              missing
              key={BuildKey(idx, val.code2, "missing")}
              seriesId={seriesId}
              episodeId={episodeId}
              mediaTitle={episode.title}
              subtitle={val}
            ></Subtitle>
          ));

          const subtitles = episode.subtitles.map((val, idx) => (
            <Subtitle
              key={BuildKey(idx, val.code2, "valid")}
              seriesId={seriesId}
              episodeId={episodeId}
              mediaTitle={episode.title}
              subtitle={val}
            ></Subtitle>
          ));

          return [...missing, ...subtitles];
        }, [episode, seriesId]);

        return (
          <Group gap="xs" wrap="nowrap">
            {elements}
          </Group>
        );
      },
    );

    const columns = useMemo<ColumnDef<Item.Episode>[]>(
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
                  monitored ? "Monitored in Sonarr" : "Unmonitored in Sonarr"
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
          header: "Episode",
          accessorKey: "episode",
        },
        {
          header: "Title",
          accessorKey: "title",
          cell: ({
            row: {
              original: { sceneName, title },
            },
          }) => {
            return (
              <TextPopover text={sceneName}>
                <Text className="table-primary">{title}</Text>
              </TextPopover>
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
          }) => <AudioList audios={audioLanguage}></AudioList>,
        },
        {
          header: "Subtitles",
          accessorKey: "missingSubtitles",
          cell: ({ row: { original } }) => {
            return <SubtitlesCell episode={original} />;
          },
        },
        {
          header: "Actions",
          cell: ({ row }) => {
            return (
              <Group gap="xs" wrap="nowrap">
                <Action
                  label="Manual Search"
                  disabled={disabled}
                  onClick={() => {
                    modals.openContextModal(EpisodeSearchModal, {
                      item: row.original,
                      download,
                      query: useEpisodesProvider,
                    });
                  }}
                  icon={faUser}
                ></Action>
                <Action
                  label="History"
                  disabled={disabled}
                  onClick={() => {
                    modals.openContextModal(
                      EpisodeHistoryModal,
                      {
                        episode: row.original,
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
      [disabled, download, modals, SubtitlesCell],
    );

    const maxSeason = useMemo(
      () =>
        episodes?.reduce<number>(
          (prev, curr) => Math.max(prev, curr.season),
          0,
        ) ?? 0,
      [episodes],
    );

    useEffect(() => {
      tableRef?.current?.setExpanded(() => ({ [`season:${maxSeason}`]: true }));
    }, [tableRef, maxSeason]);

    return (
      <GroupTable
        columns={columns}
        data={episodes ?? []}
        instanceRef={tableRef}
        onAllRowsExpandedChanged={onAllRowsExpandedChanged}
        initialState={{
          sorting: [
            { id: "season", desc: true },
            { id: "episode", desc: true },
          ],
          grouping: ["season"],
        }}
        tableStyles={{ emptyText: "No Episode Found For This Series" }}
      ></GroupTable>
    );
  },
);

export default Table;
