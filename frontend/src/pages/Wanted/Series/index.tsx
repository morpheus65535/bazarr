import {
  useEpisodeSubtitleModification,
  useEpisodeWantedPagination,
  useSeriesAction,
} from "@/apis/hooks";
import { AsyncButton } from "@/components/async";
import Language from "@/components/bazarr/Language";
import WantedView from "@/components/views/WantedView";
import { BuildKey } from "@/utilities";
import { faSearch } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { Anchor, Text } from "@mantine/core";
import { FunctionComponent, useMemo } from "react";
import { Link } from "react-router-dom";
import { Column } from "react-table";

const WantedSeriesView: FunctionComponent = () => {
  const columns: Column<Wanted.Episode>[] = useMemo<Column<Wanted.Episode>[]>(
    () => [
      {
        Header: "Name",
        accessor: "seriesTitle",
        Cell: (row) => {
          const target = `/series/${row.row.original.sonarrSeriesId}`;
          return (
            <Anchor component={Link} to={target}>
              <Text>{row.value}</Text>
            </Anchor>
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
              key={BuildKey(idx, item.code2)}
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
              <Language.Text px="xs" value={item}></Language.Text>
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
