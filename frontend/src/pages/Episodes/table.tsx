import { useDownloadEpisodeSubtitles, useEpisodesProvider } from "@/apis/hooks";
import { useShowOnlyDesired } from "@/apis/hooks/site";
import { Action, GroupTable } from "@/components";
import { EpisodeHistoryModal } from "@/components/modals";
import { EpisodeSearchModal } from "@/components/modals/ManualSearchModal";
import TextPopover from "@/components/TextPopover";
import { useModals } from "@/modules/modals";
import { BuildKey, filterSubtitleBy } from "@/utilities";
import { useProfileItemsToLanguages } from "@/utilities/languages";
import { faBookmark as farBookmark } from "@fortawesome/free-regular-svg-icons";
import {
  faBookmark,
  faHistory,
  faUser,
} from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { Badge, Group, Text } from "@mantine/core";
import { FunctionComponent, useCallback, useMemo } from "react";
import { Column } from "react-table";
import { Subtitle } from "./components";

interface Props {
  episodes: Item.Episode[] | null;
  disabled?: boolean;
  profile?: Language.Profile;
}

const Table: FunctionComponent<Props> = ({ episodes, profile, disabled }) => {
  const onlyDesired = useShowOnlyDesired();

  const profileItems = useProfileItemsToLanguages(profile);
  const { mutateAsync } = useDownloadEpisodeSubtitles();

  const download = useCallback(
    (item: Item.Episode, result: SearchResultType) => {
      const {
        language,
        hearing_impaired: hi,
        forced,
        provider,
        subtitle,
        original_format,
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
          original_format: original_format,
        },
      });
    },
    [mutateAsync]
  );

  const columns: Column<Item.Episode>[] = useMemo<Column<Item.Episode>[]>(
    () => [
      {
        accessor: "monitored",
        Cell: (row) => {
          return (
            <FontAwesomeIcon
              title={row.value ? "monitored" : "unmonitored"}
              icon={row.value ? faBookmark : farBookmark}
            ></FontAwesomeIcon>
          );
        },
      },
      {
        accessor: "season",
        Cell: (row) => {
          return `Season ${row.value}`;
        },
      },
      {
        Header: "Episode",
        accessor: "episode",
      },
      {
        Header: "Title",
        accessor: "title",
        Cell: ({ value, row }) => (
          <TextPopover text={row.original.sceneName}>
            <Text>{value}</Text>
          </TextPopover>
        ),
      },
      {
        Header: "Audio",
        accessor: "audio_language",
        Cell: (row) => {
          return row.value.map((v) => (
            <Badge color="teal" key={v.code2}>
              {v.name}
            </Badge>
          ));
        },
      },
      {
        Header: "Subtitles",
        accessor: "missing_subtitles",
        Cell: ({ row }) => {
          const episode = row.original;

          const seriesid = episode.sonarrSeriesId;

          const elements = useMemo(() => {
            const episodeid = episode.sonarrEpisodeId;

            const missing = episode.missing_subtitles.map((val, idx) => (
              <Subtitle
                missing
                key={BuildKey(idx, val.code2, "missing")}
                seriesId={seriesid}
                episodeId={episodeid}
                subtitle={val}
              ></Subtitle>
            ));

            let raw_subtitles = episode.subtitles;
            if (onlyDesired) {
              raw_subtitles = filterSubtitleBy(raw_subtitles, profileItems);
            }

            const subtitles = raw_subtitles.map((val, idx) => (
              <Subtitle
                key={BuildKey(idx, val.code2, "valid")}
                seriesId={seriesid}
                episodeId={episodeid}
                subtitle={val}
              ></Subtitle>
            ));

            return [...missing, ...subtitles];
          }, [episode, seriesid]);

          return <Group spacing="xs">{elements}</Group>;
        },
      },
      {
        Header: "Actions",
        accessor: "sonarrEpisodeId",
        Cell: ({ row }) => {
          const modals = useModals();
          return (
            <Group spacing="xs" noWrap>
              <Action
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
                disabled={disabled}
                onClick={() => {
                  modals.openContextModal(EpisodeHistoryModal, {
                    episode: row.original,
                  });
                }}
                icon={faHistory}
              ></Action>
            </Group>
          );
        },
      },
    ],
    [onlyDesired, profileItems, disabled, download]
  );

  const maxSeason = useMemo(
    () =>
      episodes?.reduce<number>(
        (prev, curr) => Math.max(prev, curr.season),
        0
      ) ?? 0,
    [episodes]
  );

  return (
    <GroupTable
      columns={columns}
      data={episodes ?? []}
      initialState={{
        sortBy: [
          { id: "season", desc: true },
          { id: "episode", desc: true },
        ],
        groupBy: ["season"],
        expanded: {
          [`season:${maxSeason}`]: true,
        },
      }}
      emptyText="No Episode Found For This Series"
    ></GroupTable>
  );
};

export default Table;
