import { FunctionComponent, useMemo } from "react";
import { Link } from "react-router-dom";
import { Column } from "react-table";
import { Anchor, Badge, Group } from "@mantine/core";
import { faSearch } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import {
  useMovieAction,
  useMovieSubtitleModification,
  useMovieWantedPagination,
} from "@/apis/hooks";
import Language from "@/components/bazarr/Language";
import { task, TaskGroup } from "@/modules/task";
import WantedView from "@/pages/views/WantedView";
import { BuildKey } from "@/utilities";

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
          const { radarrId } = wanted;

          const { download } = useMovieSubtitleModification();

          return (
            <Group gap="sm">
              {value.map((item, idx) => (
                <Badge
                  color={download.isLoading ? "gray" : undefined}
                  leftSection={<FontAwesomeIcon icon={faSearch} />}
                  key={BuildKey(idx, item.code2)}
                  style={{ cursor: "pointer" }}
                  onClick={() => {
                    task.create(
                      item.name,
                      TaskGroup.SearchSubtitle,
                      download.mutateAsync,
                      {
                        radarrId,
                        form: {
                          language: item.code2,
                          hi: item.hi,
                          forced: item.forced,
                        },
                      },
                    );
                  }}
                >
                  <Language.Text value={item}></Language.Text>
                </Badge>
              ))}
            </Group>
          );
        },
      },
    ],
    [],
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
