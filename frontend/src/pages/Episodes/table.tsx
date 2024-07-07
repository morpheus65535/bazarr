import React, { forwardRef, useCallback, useEffect, useMemo } from "react";
import { Group, Text } from "@mantine/core";
import { faBookmark as farBookmark } from "@fortawesome/free-regular-svg-icons";
import {
  faBookmark,
  faHistory,
  faUser,
} from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { ColumnDef, Table as TableInstance } from "@tanstack/react-table";
import { useDownloadEpisodeSubtitles, useEpisodesProvider } from "@/apis/hooks";
import { useShowOnlyDesired } from "@/apis/hooks/site";
import { Action, GroupTable } from "@/components";
import { AudioList } from "@/components/bazarr";
import { EpisodeHistoryModal } from "@/components/modals";
import { EpisodeSearchModal } from "@/components/modals/ManualSearchModal";
import TextPopover from "@/components/TextPopover";
import { useModals } from "@/modules/modals";
import { BuildKey, filterSubtitleBy } from "@/utilities";
import { useProfileItemsToLanguages } from "@/utilities/languages";
import { Subtitle } from "./components";

interface Props {
  episodes: Item.Episode[] | null;
  disabled?: boolean;
  profile?: Language.Profile;
  onAllRowsExpandedChanged: (isAllRowsExpanded: boolean) => void;
}

const Table = forwardRef<TableInstance<Item.Episode> | null, Props>(
  ({ episodes, profile, disabled, onAllRowsExpandedChanged }, ref) => {
    const onlyDesired = useShowOnlyDesired();

    const tableRef =
      ref as React.MutableRefObject<TableInstance<Item.Episode> | null>;

    const profileItems = useProfileItemsToLanguages(profile);

    const { mutateAsync } = useDownloadEpisodeSubtitles();

    const modals = useModals();

    const download = useCallback(
      (item: Item.Episode, result: SearchResultType) => {
        const {
          language,
          hearing_impaired: hi,
          forced,
          provider,
          subtitle,
          original_format: originalFormat,
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
            // eslint-disable-next-line camelcase
            original_format: originalFormat,
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

          const missing = episode.missing_subtitles.map((val, idx) => (
            <Subtitle
              missing
              key={BuildKey(idx, val.code2, "missing")}
              seriesId={seriesId}
              episodeId={episodeId}
              subtitle={val}
            ></Subtitle>
          ));

          let rawSubtitles = episode.subtitles;
          if (onlyDesired) {
            rawSubtitles = filterSubtitleBy(rawSubtitles, profileItems);
          }

          const subtitles = rawSubtitles.map((val, idx) => (
            <Subtitle
              key={BuildKey(idx, val.code2, "valid")}
              seriesId={seriesId}
              episodeId={episodeId}
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
              <FontAwesomeIcon
                title={monitored ? "monitored" : "unmonitored"}
                icon={monitored ? faBookmark : farBookmark}
              ></FontAwesomeIcon>
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
          accessorKey: "audio_language",
          cell: ({
            row: {
              original: { audio_language: audioLanguage },
            },
          }) => <AudioList audios={audioLanguage}></AudioList>,
        },
        {
          header: "Subtitles",
          accessorKey: "missing_subtitles",
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
