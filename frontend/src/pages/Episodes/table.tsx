import { useDownloadEpisodeSubtitles, useEpisodesProvider } from "@/apis/hooks";
import { useShowOnlyDesired } from "@/apis/hooks/site";
import { Action, GroupTable } from "@/components";
import { AudioList } from "@/components/bazarr";
import { EpisodeHistoryModal } from "@/components/modals";
import { EpisodeSearchModal } from "@/components/modals/ManualSearchModal";
import TextPopover from "@/components/TextPopover";
import { useModals } from "@/modules/modals";
import { useTableStyles } from "@/styles";
import { BuildKey, filterSubtitleBy } from "@/utilities";
import { useProfileItemsToLanguages } from "@/utilities/languages";
import { faBookmark as farBookmark } from "@fortawesome/free-regular-svg-icons";
import {
  faBookmark,
  faHistory,
  faUser,
} from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { Group, Text } from "@mantine/core";
import {
  FunctionComponent,
  useCallback,
  useEffect,
  useMemo,
  useRef,
} from "react";
import { Column, TableInstance } from "react-table";
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
          original_format,
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
        Cell: ({ value, row }) => {
          const { classes } = useTableStyles();

          return (
            <TextPopover text={row.original.sceneName}>
              <Text className={classes.primary}>{value}</Text>
            </TextPopover>
          );
        },
      },
      {
        Header: "Audio",
        accessor: "audio_language",
        Cell: ({ value }) => <AudioList audios={value}></AudioList>,
      },
      {
        Header: "Subtitles",
        accessor: "missing_subtitles",
        Cell: ({ row }) => {
          const episode = row.original;

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

            let raw_subtitles = episode.subtitles;
            if (onlyDesired) {
              raw_subtitles = filterSubtitleBy(raw_subtitles, profileItems);
            }

            const subtitles = raw_subtitles.map((val, idx) => (
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
            <Group spacing="xs" noWrap>
              {elements}
            </Group>
          );
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
                label="Manual Search"
                disabled={disabled}
                color="dark"
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
                color="dark"
                onClick={() => {
                  modals.openContextModal(
                    EpisodeHistoryModal,
                    {
                      episode: row.original,
                    },
                    {
                      title: `History - ${row.original.title}`,
                    }
                  );
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

  const instance = useRef<TableInstance<Item.Episode> | null>(null);

  useEffect(() => {
    if (instance.current) {
      instance.current.toggleRowExpanded([`season:${maxSeason}`], true);
    }
  }, [maxSeason]);

  return (
    <GroupTable
      columns={columns}
      data={episodes ?? []}
      instanceRef={instance}
      initialState={{
        sortBy: [
          { id: "season", desc: true },
          { id: "episode", desc: true },
        ],
        groupBy: ["season"],
      }}
      tableStyles={{ emptyText: "No Episode Found For This Series" }}
    ></GroupTable>
  );
};

export default Table;
