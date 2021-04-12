import { faBookmark as farBookmark } from "@fortawesome/free-regular-svg-icons";
import {
  faBookmark,
  faBriefcase,
  faHistory,
  faUser,
} from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import React, { FunctionComponent, useCallback, useMemo } from "react";
import { Badge, ButtonGroup } from "react-bootstrap";
import { Column, TableUpdater } from "react-table";
import { useProfileItems } from "../../@redux/hooks";
import { ProvidersApi } from "../../apis";
import {
  ActionButton,
  AsyncStateOverlay,
  EpisodeHistoryModal,
  GroupTable,
  SubtitleToolModal,
  TextPopover,
  useShowModal,
} from "../../components";
import { ManualSearchModal } from "../../components/modals/ManualSearchModal";
import { BuildKey, useShowOnlyDesired } from "../../utilites";
import { SubtitleAction } from "./components";

interface Props {
  episodes: AsyncState<Item.Episode[]>;
  profile?: Profile.Languages;
}

const download = (item: any, result: SearchResultType) => {
  item = item as Item.Episode;
  const { language, hearing_impaired, forced, provider, subtitle } = result;
  return ProvidersApi.downloadEpisodeSubtitle(
    item.sonarrSeriesId,
    item.sonarrEpisodeId,
    {
      language,
      hi: hearing_impaired,
      forced,
      provider,
      subtitle,
    }
  );
};

const Table: FunctionComponent<Props> = ({ episodes, profile }) => {
  const showModal = useShowModal();

  const onlyDesired = useShowOnlyDesired();

  const profileItems = useProfileItems(profile);

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
        className: "text-nowrap",
        Cell: ({ value, row }) => (
          <TextPopover text={row.original.sceneName} delay={1}>
            <span>{value}</span>
          </TextPopover>
        ),
      },
      {
        Header: "Audio",
        accessor: "audio_language",
        Cell: (row) => {
          return row.value.map((v) => (
            <Badge variant="secondary" key={v.code2}>
              {v.name}
            </Badge>
          ));
        },
      },
      {
        Header: "Subtitles",
        accessor: "missing_subtitles",
        Cell: ({ row, loose }) => {
          const episode = row.original;

          const seriesid = episode.sonarrSeriesId;

          const desired = loose![0] as boolean;
          const items = loose![1] as Language[];

          const elements = useMemo(() => {
            const episodeid = episode.sonarrEpisodeId;

            const missing = episode.missing_subtitles.map((val, idx) => (
              <SubtitleAction
                missing
                key={BuildKey(idx, val.code2, "missing")}
                seriesid={seriesid}
                episodeid={episodeid}
                subtitle={val}
              ></SubtitleAction>
            ));

            let existing = episode.subtitles;
            if (desired) {
              existing = existing.filter(
                (v) => items.findIndex((inn) => inn.code2 === v.code2) !== -1
              );
            }

            const subtitles = existing.map((val, idx) => (
              <SubtitleAction
                key={BuildKey(idx, val.code2, "valid")}
                seriesid={seriesid}
                episodeid={episodeid}
                subtitle={val}
              ></SubtitleAction>
            ));

            return [...missing, ...subtitles];
          }, [episode, seriesid, desired, items]);

          return elements;
        },
      },
      {
        Header: "Actions",
        accessor: "sonarrEpisodeId",
        Cell: ({ row, externalUpdate }) => {
          return (
            <ButtonGroup>
              <ActionButton
                icon={faUser}
                onClick={() => {
                  externalUpdate && externalUpdate(row, "manual-search");
                }}
              ></ActionButton>
              <ActionButton
                icon={faHistory}
                onClick={() => {
                  externalUpdate && externalUpdate(row, "history");
                }}
              ></ActionButton>
              <ActionButton
                icon={faBriefcase}
                onClick={() => {
                  externalUpdate && externalUpdate(row, "tools");
                }}
              ></ActionButton>
            </ButtonGroup>
          );
        },
      },
    ],
    []
  );

  const updateRow = useCallback<TableUpdater<Item.Episode>>(
    (row, modalKey: string) => {
      if (modalKey === "tools") {
        showModal(modalKey, [row.original]);
      } else {
        showModal(modalKey, row.original);
      }
    },
    [showModal]
  );

  const maxSeason = useMemo(
    () =>
      episodes.data.reduce<number>(
        (prev, curr) => Math.max(prev, curr.season),
        0
      ),
    [episodes]
  );

  return (
    <React.Fragment>
      <AsyncStateOverlay state={episodes}>
        {(data) => (
          <GroupTable
            columns={columns}
            data={data}
            externalUpdate={updateRow}
            loose={[onlyDesired, profileItems]}
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
        )}
      </AsyncStateOverlay>
      <SubtitleToolModal modalKey="tools" size="lg"></SubtitleToolModal>
      <EpisodeHistoryModal modalKey="history" size="lg"></EpisodeHistoryModal>
      <ManualSearchModal
        modalKey="manual-search"
        onSelect={download}
      ></ManualSearchModal>
    </React.Fragment>
  );
};

export default Table;
