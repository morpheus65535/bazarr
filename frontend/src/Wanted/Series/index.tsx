import { faSearch } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import React, { FunctionComponent, useMemo } from "react";
import { Badge } from "react-bootstrap";
import { Link } from "react-router-dom";
import { Column } from "react-table";
import {
  useEpisodeSubtitleModification,
  useEpisodeWantedPagination,
  useSeriesAction,
} from "src/apis/hooks";
import { AsyncButton, LanguageText } from "../../components";
import WantedView from "../../components/views/WantedView";
import { BuildKey } from "../../utilities";

interface Props {}

const WantedSeriesView: FunctionComponent<Props> = () => {
  const columns: Column<Wanted.Episode>[] = useMemo<Column<Wanted.Episode>[]>(
    () => [
      {
        Header: "Name",
        accessor: "seriesTitle",
        Cell: (row) => {
          const target = `/series/${row.row.original.sonarrSeriesId}`;
          return (
            <Link to={target}>
              <span>{row.value}</span>
            </Link>
          );
        },
      },
      {
        Header: "Episode",
        accessor: "episode_number",
      },
      {
        accessor: "episodeTitle",
      },
      {
        Header: "Missing",
        accessor: "missing_subtitles",
        Cell: ({ row, value }) => {
          const wanted = row.original;
          const hi = wanted.hearing_impaired;
          const seriesId = wanted.sonarrSeriesId;
          const episodeId = wanted.sonarrEpisodeId;

          const { download } = useEpisodeSubtitleModification();

          return value.map((item, idx) => (
            <AsyncButton
              as={Badge}
              key={BuildKey(idx, item.code2)}
              className="mx-1 mr-2"
              variant="secondary"
              promise={() =>
                download.mutateAsync({
                  seriesId,
                  episodeId,
                  form: {
                    language: item.code2,
                    hi,
                    forced: false,
                  },
                })
              }
            >
              <LanguageText className="pr-1" text={item}></LanguageText>
              <FontAwesomeIcon size="sm" icon={faSearch}></FontAwesomeIcon>
            </AsyncButton>
          ));
        },
      },
    ],
    []
  );

  const { mutateAsync } = useSeriesAction();
  const query = useEpisodeWantedPagination();
  return (
    <WantedView
      name="Series"
      columns={columns}
      query={query}
      searchAll={() => mutateAsync({ action: "search-wanted" })}
    ></WantedView>
  );
};

export default WantedSeriesView;
