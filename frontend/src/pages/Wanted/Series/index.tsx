import {
  useEpisodeSubtitleModification,
  useEpisodeWantedPagination,
  useSeriesAction,
} from "@/apis/hooks";
import MutateButton from "@/components/async/MutateButton";
import Language from "@/components/bazarr/Language";
import WantedView from "@/pages/views/WantedView";
import { BuildKey } from "@/utilities";
import { faSearch } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { Anchor, Group } from "@mantine/core";
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
              {row.value}
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

          return (
            <Group spacing="sm">
              {value.map((item, idx) => (
                <MutateButton
                  key={BuildKey(idx, item.code2)}
                  compact
                  size="xs"
                  mutation={download}
                  leftIcon={<FontAwesomeIcon icon={faSearch} />}
                  args={() => ({
                    seriesId,
                    episodeId,
                    form: {
                      language: item.code2,
                      hi,
                      forced: false,
                    },
                  })}
                >
                  <Language.Text px="xs" value={item}></Language.Text>
                </MutateButton>
              ))}
            </Group>
          );
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
