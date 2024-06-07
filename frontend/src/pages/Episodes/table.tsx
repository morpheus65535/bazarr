import { useDownloadEpisodeSubtitles, useEpisodesProvider } from "@/apis/hooks";
import { useShowOnlyDesired } from "@/apis/hooks/site";
import { Action, GroupTable } from "@/components";
import TextPopover from "@/components/TextPopover";
import { AudioList } from "@/components/bazarr";
import { EpisodeHistoryModal } from "@/components/modals";
import { EpisodeSearchModal } from "@/components/modals/ManualSearchModal";
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
  expand?: boolean;
  initial?: boolean;
}

const Table: FunctionComponent<Props> = ({
  episodes,
  profile,
  disabled,
  expand,
  initial,
}) => {
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
          return <Text span>Season {row.value}</Text>;
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
          return (
            <TextPopover text={row.original.sceneName}>
              <Text className="table-primary">{value}</Text>
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
      },
      {
        Header: "Actions",
        accessor: "sonarrEpisodeId",
        Cell: ({ row }) => {
          const modals = useModals();
          return (
            <Group gap="xs" wrap="nowrap">
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
    [onlyDesired, profileItems, disabled, download],
  );

  const maxSeason = useMemo(
    () =>
      episodes?.reduce<number>(
        (prev, curr) => Math.max(prev, curr.season),
        0,
      ) ?? 0,
    [episodes],
  );

  const instance = useRef<TableInstance<Item.Episode> | null>(null);

  useEffect(() => {
    if (instance.current) {
      if (initial) {
        // start with all rows collapsed
        instance.current.toggleAllRowsExpanded(false);
        // expand the last/current season on initial display
        instance.current.toggleRowExpanded([`season:${maxSeason}`], true);
      } else {
        if (expand !== undefined) {
          instance.current.toggleAllRowsExpanded(expand);
        }
      }
    }
  }, [maxSeason, expand, initial]);

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
