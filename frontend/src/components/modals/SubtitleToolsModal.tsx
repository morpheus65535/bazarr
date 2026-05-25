import { FunctionComponent, useCallback, useMemo, useState } from "react";
import {
  Badge,
  Button,
  Checkbox,
  Divider,
  Group,
  Paper,
  Select,
  Stack,
  Table,
  Text,
  TextInput,
} from "@mantine/core";
import {
  faPlus,
  faSort,
  faSortDown,
  faSortUp,
  faXmark,
} from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import {
  ColumnDef,
  flexRender,
  getFilteredRowModel,
  getSortedRowModel,
  Header,
  SortingState,
} from "@tanstack/react-table";
import {
  useEpisodeSubtitleModification,
  useMovieSubtitleModification,
} from "@/apis/hooks";
import Language from "@/components/bazarr/Language";
import SubtitleToolsMenu from "@/components/SubtitleToolsMenu";
import SimpleTable from "@/components/tables/SimpleTable";
import { useModals, withModal } from "@/modules/modals";
import { fromPython, isMovie, toPython } from "@/utilities";

type SupportType = Item.Episode | Item.Movie;

type TableColumnType = FormType.ModifySubtitle & {
  raw_language: Language.Info;
  episode?: number;
  episodeLabel: string;
  seriesId: number;
  season?: number;
  name: string;
  isMovie: boolean;
};

type FilterCategory = "language" | "season" | "episode" | "item" | "file";

type SubtitleFilter = {
  category: FilterCategory;
  label: string;
  value: string;
};

const filterOptions: { label: string; value: FilterCategory }[] = [
  { label: "Language", value: "language" },
  { label: "Season", value: "season" },
  { label: "Episode", value: "episode" },
  { label: "Title", value: "item" },
  { label: "File", value: "file" },
];

type LocalisedType = {
  id: number;
  seriesId: number;
  type: "movie" | "episode";
  name: string;
  isMovie: boolean;
};

function getLocalisedValues(item: SupportType): LocalisedType {
  if (isMovie(item)) {
    return {
      seriesId: 0,
      id: item.radarrId,
      type: "movie",
      name: item.title,
      isMovie: true,
    };
  } else {
    return {
      seriesId: item.sonarrSeriesId,
      id: item.sonarrEpisodeId,
      type: "episode",
      name: item.title,
      isMovie: false,
    };
  }
}

const CanSelectSubtitle = (item: TableColumnType) => {
  return item.path.endsWith(".srt");
};

function getFilterKey(filter: SubtitleFilter) {
  return `${filter.category}:${filter.value}`;
}

function getLanguageValue(language: Language.Info) {
  const { code2, hi, forced } = language;

  return `${code2}${hi ? ":hi" : ""}${forced ? ":forced" : ""}`;
}

function getEpisodeLabel(item: SupportType) {
  if (isMovie(item)) {
    return "";
  }

  const {
    episode,
    episode_number: episodeNumber,
    season,
  } = item as Item.Episode & {
    episode_number?: string;
  };

  if (season === undefined || episode === undefined) {
    return episodeNumber ?? "";
  }

  return `S${season.toString().padStart(2, "0")}E${episode
    .toString()
    .padStart(2, "0")}`;
}

interface SubtitleToolViewProps {
  payload: SupportType[];
}

const SubtitleToolView: FunctionComponent<SubtitleToolViewProps> = ({
  payload,
}) => {
  const [selections, setSelections] = useState<TableColumnType[]>([]);
  const [filterCategory, setFilterCategory] =
    useState<FilterCategory>("language");
  const [filterValue, setFilterValue] = useState("");
  const [filters, setFilters] = useState<SubtitleFilter[]>([]);
  const [sorting, setSorting] = useState<SortingState>([
    { id: "episodeLabel", desc: false },
  ]);
  const { remove: removeEpisode, download: downloadEpisode } =
    useEpisodeSubtitleModification();
  const { download: downloadMovie, remove: removeMovie } =
    useMovieSubtitleModification();
  const modals = useModals();

  const columns = useMemo<ColumnDef<TableColumnType>[]>(
    () => [
      {
        id: "selection",
        enableGlobalFilter: false,
        enableSorting: false,
        header: ({ table }) => {
          return (
            <Checkbox
              id="table-header-selection"
              indeterminate={table.getIsSomeRowsSelected()}
              checked={table.getIsAllRowsSelected()}
              onChange={table.getToggleAllRowsSelectedHandler()}
            ></Checkbox>
          );
        },
        cell: ({ row: { index, getIsSelected, getToggleSelectedHandler } }) => {
          return (
            <Checkbox
              id={`table-cell-${index}`}
              checked={getIsSelected()}
              onChange={getToggleSelectedHandler()}
              onClick={getToggleSelectedHandler()}
            ></Checkbox>
          );
        },
      },
      {
        header: "Language",
        accessorKey: "language",
        cell: ({
          row: {
            original: { raw_language: rawLanguage },
          },
        }) => (
          <Badge color="secondary">
            <Language.Text value={rawLanguage} long></Language.Text>
          </Badge>
        ),
      },
      {
        header: "Episode",
        accessorKey: "episodeLabel",
      },
      {
        header: "Title",
        accessorKey: "name",
      },
      {
        id: "file",
        header: "File",
        accessorKey: "path",
        cell: ({
          row: {
            original: { path },
          },
        }) => {
          let idx = path.lastIndexOf("/");

          if (idx === -1) {
            idx = path.lastIndexOf("\\");
          }

          if (idx !== -1) {
            return <Text>{path.slice(idx + 1)}</Text>;
          } else {
            return <Text>{path}</Text>;
          }
        },
      },
    ],
    [],
  );

  const data = useMemo<TableColumnType[]>(
    () =>
      payload.flatMap((item) => {
        const {
          seriesId,
          id,
          type,
          name,
          isMovie: isMovieItem,
        } = getLocalisedValues(item);
        const episodeLabel = getEpisodeLabel(item);
        return item.subtitles.flatMap((v) => {
          if (v.path) {
            return [
              {
                id,
                seriesId,
                type,
                episode: isMovie(item) ? undefined : item.episode,
                episodeLabel,
                language: v.code2,
                path: v.path,
                // eslint-disable-next-line camelcase
                raw_language: v,
                season: isMovie(item) ? undefined : item.season,
                name,
                hi: toPython(v.hi),
                forced: toPython(v.forced),
                isMovie: isMovieItem,
              },
            ];
          } else {
            return [];
          }
        });
      }),
    [payload],
  );

  const filterValues = useMemo(() => {
    const language = new Map<string, string>();
    const season = new Map<string, string>();
    const episode = new Map<string, string>();
    const item = new Map<string, string>();

    data.forEach((row) => {
      const languageValue = getLanguageValue(row.raw_language);
      language.set(languageValue, languageValue);
      item.set(row.name.toLowerCase(), row.name);

      if (row.season !== undefined) {
        season.set(row.season.toString(), `Season ${row.season}`);
      }

      if (row.episodeLabel) {
        episode.set(row.episodeLabel.toLowerCase(), row.episodeLabel);
      }
    });

    return {
      episode: [...episode].map(([value, label]) => ({ label, value })),
      file: [],
      item: [...item].map(([value, label]) => ({ label, value })),
      language: [...language].map(([value, label]) => ({ label, value })),
      season: [...season]
        .sort(([a], [b]) => Number(a) - Number(b))
        .map(([value, label]) => ({ label, value })),
    };
  }, [data]);

  const currentFilterOptions = filterValues[filterCategory];
  const selectedFilterOption = currentFilterOptions.find(
    (option) => option.value === filterValue,
  );

  const addFilter = useCallback(() => {
    const value = filterValue.trim();

    if (value.length === 0) {
      return;
    }

    const filter: SubtitleFilter = {
      category: filterCategory,
      label: selectedFilterOption?.label ?? value,
      value: value.toLowerCase(),
    };

    setFilters((current) => {
      if (current.some((item) => getFilterKey(item) === getFilterKey(filter))) {
        return current;
      }

      return [...current, filter];
    });
    setFilterValue("");
  }, [filterCategory, filterValue, selectedFilterOption?.label]);

  const removeFilter = useCallback((filter: SubtitleFilter) => {
    setFilters((current) =>
      current.filter((item) => getFilterKey(item) !== getFilterKey(filter)),
    );
  }, []);

  const renderHeaders = useCallback(
    (headers: Header<TableColumnType, unknown>[]) =>
      headers.map((header) => {
        const canSort = header.column.getCanSort();
        const sorted = header.column.getIsSorted();
        const icon =
          sorted === "asc" ? faSortUp : sorted === "desc" ? faSortDown : faSort;

        return (
          <Table.Th
            key={header.id}
            onClick={header.column.getToggleSortingHandler()}
            style={{
              cursor: canSort ? "pointer" : undefined,
              userSelect: canSort ? "none" : undefined,
              whiteSpace: "nowrap",
            }}
          >
            {flexRender(header.column.columnDef.header, header.getContext())}
            {canSort && (
              <FontAwesomeIcon
                icon={icon}
                style={{ marginLeft: "0.5rem" }}
              ></FontAwesomeIcon>
            )}
          </Table.Th>
        );
      }),
    [],
  );

  return (
    <Stack>
      <SimpleTable
        tableStyles={{
          emptyText: "No external subtitles found",
          headersRenderer: renderHeaders,
        }}
        enableRowSelection={(row) => CanSelectSubtitle(row.original)}
        enableSorting
        enableGlobalFilter
        globalFilterFn={(row, _columnId, value) => {
          const activeFilters = Array.isArray(value) ? value : [];

          if (activeFilters.length === 0) {
            return true;
          }

          return activeFilters.every((filter: SubtitleFilter) => {
            const { original } = row;

            switch (filter.category) {
              case "episode":
                return original.episodeLabel.toLowerCase() === filter.value;
              case "file":
                return original.path.toLowerCase().includes(filter.value);
              case "item":
                return original.name.toLowerCase().includes(filter.value);
              case "language":
                return getLanguageValue(original.raw_language) === filter.value;
              case "season":
                return original.season?.toString() === filter.value;
            }
          });
        }}
        getFilteredRowModel={getFilteredRowModel()}
        getSortedRowModel={getSortedRowModel()}
        onRowSelectionChanged={(rows) =>
          setSelections(rows.map((r) => r.original))
        }
        onSortingChange={setSorting}
        state={{ globalFilter: filters, sorting }}
        columns={columns}
        data={data}
      ></SimpleTable>
      <Paper
        withBorder
        p="sm"
        style={{ bottom: 0, position: "sticky", zIndex: 10 }}
      >
        <Stack gap="xs">
          <Group justify="space-between">
            <SubtitleToolsMenu
              selections={selections}
              onAction={(action) => {
                selections.forEach(async (selection) => {
                  const actionPayload = {
                    form: {
                      language: selection.language,
                      hi: fromPython(selection.hi),
                      forced: fromPython(selection.forced),
                      path: selection.path,
                    },
                    radarrId: 0,
                    seriesId: 0,
                    episodeId: 0,
                  };
                  if (selection.isMovie) {
                    actionPayload.radarrId = selection.id;
                  } else {
                    actionPayload.seriesId = selection.seriesId;
                    actionPayload.episodeId = selection.id;
                  }
                  const download = selection.isMovie
                    ? downloadMovie
                    : downloadEpisode;
                  const remove = selection.isMovie
                    ? removeMovie
                    : removeEpisode;

                  if (action === "search") {
                    await download.mutateAsync(actionPayload);
                  } else if (action === "delete" && selection.path) {
                    await remove.mutateAsync(actionPayload);
                  }
                });
                modals.closeAll();
              }}
            >
              <Button disabled={selections.length === 0} variant="light">
                Select Action
              </Button>
            </SubtitleToolsMenu>
            <Group gap="xs" align="end">
              <Select
                data={filterOptions}
                label="Filter"
                value={filterCategory}
                onChange={(value) => {
                  setFilterCategory((value as FilterCategory) ?? "language");
                  setFilterValue("");
                }}
              ></Select>
              {filterCategory === "file" ? (
                <TextInput
                  label="Value"
                  value={filterValue}
                  onChange={(event) => {
                    setFilterValue(event.currentTarget.value);
                  }}
                  onKeyDown={(event) => {
                    if (event.key === "Enter") {
                      addFilter();
                    }
                  }}
                ></TextInput>
              ) : (
                <Select
                  searchable
                  data={currentFilterOptions}
                  label="Value"
                  value={filterValue}
                  onChange={(value) => {
                    setFilterValue(value ?? "");
                  }}
                ></Select>
              )}
              <Button
                leftSection={<FontAwesomeIcon icon={faPlus}></FontAwesomeIcon>}
                disabled={filterValue.length === 0}
                onClick={addFilter}
              >
                Add
              </Button>
            </Group>
          </Group>
          <Divider></Divider>
          <Group gap="xs">
            {filters.length === 0 ? (
              <Text c="dimmed" size="sm">
                No filters applied
              </Text>
            ) : (
              filters.map((filter) => {
                const category = filterOptions.find(
                  (option) => option.value === filter.category,
                );

                return (
                  <Button
                    key={getFilterKey(filter)}
                    size="xs"
                    variant="light"
                    rightSection={
                      <FontAwesomeIcon icon={faXmark}></FontAwesomeIcon>
                    }
                    onClick={() => removeFilter(filter)}
                  >
                    {category?.label}: {filter.label}
                  </Button>
                );
              })
            )}
          </Group>
        </Stack>
      </Paper>
    </Stack>
  );
};

export default withModal(SubtitleToolView, "subtitle-tools", {
  title: "Subtitle Tools",
  size: "xl",
});
