import {
  useMovieAction,
  useMovieSubtitleModification,
  useMovieWantedPagination,
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

const WantedMoviesView: FunctionComponent = () => {
  const columns: Column<Wanted.Movie>[] = useMemo<Column<Wanted.Movie>[]>(
    () => [
      {
        Header: "Name",
        accessor: "title",
        Cell: (row) => {
          const target = `/movies/${row.row.original.radarrId}`;
          return (
            <Anchor component={Link} to={target}>
              {row.value}
            </Anchor>
          );
        },
      },
      {
        Header: "Missing",
        accessor: "missing_subtitles",
        Cell: ({ row, value }) => {
          const wanted = row.original;
          const { hearing_impaired: hi, radarrId } = wanted;

          const { download } = useMovieSubtitleModification();

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
                    radarrId,
                    form: {
                      language: item.code2,
                      hi,
                      forced: false,
                    },
                  })}
                >
                  <Language.Text pr="xs" value={item}></Language.Text>
                </MutateButton>
              ))}
            </Group>
          );
        },
      },
    ],
    []
  );

  const { mutateAsync } = useMovieAction();
  const query = useMovieWantedPagination();

  return (
    <WantedView
      name="Movies"
      columns={columns}
      query={query}
      searchAll={() => mutateAsync({ action: "search-wanted" })}
    ></WantedView>
  );
};

export default WantedMoviesView;
