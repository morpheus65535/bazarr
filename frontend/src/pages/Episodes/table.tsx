import { useDownloadEpisodeSubtitles, useEpisodesProvider } from "@/apis/hooks";
import { Action, GroupTable } from "@/components";
import { EpisodeHistoryModal } from "@/components/modals";
import { EpisodeSearchModal } from "@/components/modals/ManualSearchModal";
import SubtitleTools, {
  SubtitleToolModal,
} from "@/components/modals/subtitle-tools";
import TextPopover from "@/components/TextPopover";
import { useModalControl } from "@/modules/modals";
import { useShowOnlyDesired } from "@/modules/redux/hooks";
import { BuildKey, filterSubtitleBy } from "@/utilities";
import { useProfileItemsToLanguages } from "@/utilities/languages";
import { faBookmark as farBookmark } from "@fortawesome/free-regular-svg-icons";
import {
  faBookmark,
  faBriefcase,
  faHistory,
  faUser,
} from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { Badge, Group, Text } from "@mantine/core";
import { FunctionComponent, useCallback, useMemo } from "react";
import { Column } from "react-table";
import { Subtitle } from "./components";

interface Props {
  series?: Item.Series;
  episodes: Item.Episode[];
  disabled?: boolean;
  profile?: Language.Profile;
}

const Table: FunctionComponent<Props> = ({
  series,
  episodes,
  profile,
  disabled,
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
          const { show } = useModalControl();
          return (
            <Group spacing="xs" noWrap>
              <Action
                disabled={series?.profileId === null || disabled}
                onClick={() => {
                  show(EpisodeSearchModal, row.original);
                }}
                icon={faUser}
              ></Action>
              <Action
                disabled={disabled}
                onClick={() => {
                  show(EpisodeHistoryModal, row.original);
                }}
                icon={faHistory}
              ></Action>
              <Action
                disabled={disabled}
                onClick={() => {
                  show(SubtitleToolModal, [row.original]);
                }}
                icon={faBriefcase}
              ></Action>
            </Group>
          );
        },
      },
    ],
    [onlyDesired, profileItems, series, disabled]
  );

  const maxSeason = useMemo(
    () =>
      episodes.reduce<number>((prev, curr) => Math.max(prev, curr.season), 0),
    [episodes]
  );

  return (
    <>
      <GroupTable
        columns={columns}
        data={episodes}
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
      <SubtitleTools></SubtitleTools>
      <EpisodeHistoryModal></EpisodeHistoryModal>
      <EpisodeSearchModal
        download={download}
        query={useEpisodesProvider}
      ></EpisodeSearchModal>
    </>
  );
};

export default Table;
