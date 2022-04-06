import {
  useMovieAction,
  useMovieSubtitleModification,
  useMovieWantedPagination,
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
              <Text>{row.value}</Text>
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

          return value.map((item, idx) => (
            <AsyncButton
              key={BuildKey(idx, item.code2)}
              promise={() =>
                download.mutateAsync({
                  radarrId,
                  form: {
                    language: item.code2,
                    hi,
                    forced: false,
                  },
                })
              }
            >
              <Language.Text pr="xs" value={item}></Language.Text>
              <FontAwesomeIcon size="sm" icon={faSearch}></FontAwesomeIcon>
            </AsyncButton>
          ));
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
