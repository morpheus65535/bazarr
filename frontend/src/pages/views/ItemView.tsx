import {
  ComponentProps,
  ReactNode,
  useCallback,
  useEffect,
  useEffectEvent,
  useMemo,
  useRef,
  useState,
} from "react";
import { useLocation, useNavigate } from "react-router";
import {
  Button,
  ButtonProps,
  Group,
  Indicator,
  Menu,
  Pill,
  Popover,
  SegmentedControl,
  Stack,
  Table,
} from "@mantine/core";
import { useMergedRef, useResizeObserver } from "@mantine/hooks";
import { IconDefinition } from "@fortawesome/fontawesome-common-types";
import {
  faCaretDown,
  faCaretUp,
  faCheck,
  faFilter,
  faList,
  faSort,
  faTableCellsLarge,
  faTableList,
} from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { QueryKey, UseQueryResult } from "@tanstack/react-query";
import { flexRender } from "@tanstack/react-table";
import { useLanguageProfiles, useLanguages } from "@/apis/hooks";
import {
  useInfinitePaginationQuery,
  usePaginationQuery,
} from "@/apis/queries/hooks";
import {
  MultiSelector,
  QueryPageTable,
  QueryPosterGrid,
  Selector,
  SelectorOption,
  Toolbox,
} from "@/components";
import {
  AppColumnDef as ColumnDef,
  AppHeader as Header,
} from "@/components/tables/features";
import { useListQueryState } from "@/utilities";
import { useViewMode, ViewMode } from "@/utilities/viewMode";

const EMPTY_TAGS: string[] = [];
const MAX_VISIBLE_TAGS = 2;

const ToolboxIconButton = ({
  icon,
  children,
  ...props
}: { icon: IconDefinition } & ButtonProps &
  Omit<ComponentProps<"button">, "ref">) => (
  <Button
    variant="subtle"
    color="gray"
    size="xs"
    leftSection={<FontAwesomeIcon icon={icon} size="lg" />}
    styles={{
      root: { height: "auto", padding: "6px 12px" },
      inner: { flexDirection: "column", gap: 6 },
      section: { marginInlineEnd: 0 },
    }}
    {...props}
  >
    {children}
  </Button>
);

interface SortField {
  value: string;
  label: string;
}

interface FilterConfig {
  sortFields: SortField[];
  filters?: {
    monitored?: boolean;
    missing?: boolean;
    profile?: boolean;
    audio?: boolean;
    tags?: boolean;
  };
}

type SetFilter = <K extends keyof Parameter.ListFilters>(
  key: K,
  value: Parameter.ListFilters[K] | undefined,
) => void;

interface Props<T extends Item.Base = Item.Base> {
  queryKey: QueryKey;
  queryFn: RangeQuery<T>;
  columns: ColumnDef<T>[];
  // Enables the table/poster toggle when both are provided. The key is used
  // to persist the selection in the browser.
  viewModeKey?: string;
  renderPoster?: (item: T) => ReactNode;
  filterConfig: FilterConfig;
  // Required when filterConfig.filters.tags is set: fetches the full list of
  // tags in use, independent of the currently loaded/filtered items.
  useTags?: () => Pick<UseQueryResult<string[]>, "data">;
  // Scopes the filter/sort URL params (e.g. "series_sort_by") so state does
  // not bleed between pages sharing this view.
  statePrefix?: string;
}

interface FilterControlsProps {
  query: Parameter.ListState;
  filterConfig: FilterConfig;
  tagOptions: SelectorOption<string>[];
  setFilter: SetFilter;
}

interface TagsFilterProps {
  value: string[];
  options: SelectorOption<string>[];
  onChange: (value: string[] | undefined) => void;
}

// Keeps the selected tags in local state so picking an option does not push a
// URL change (which closes the dropdown). The URL is updated once the dropdown
// closes or the control unmounts (e.g. the mobile popover closes).
const TagsFilterSelector = ({ value, options, onChange }: TagsFilterProps) => {
  const [localValue, setLocalValue] = useState<string[]>(value);
  const dirty = useRef(false);

  useEffect(() => {
    setLocalValue(value);
    dirty.current = false;
  }, [value]);

  const commit = (tags: string[]) => {
    if (dirty.current) {
      dirty.current = false;
      onChange(tags.length === 0 ? undefined : tags);
    }
  };

  const commitOnUnmount = useEffectEvent(() => commit(localValue));
  useEffect(() => commitOnUnmount, []);

  return (
    <MultiSelector<string>
      size="sm"
      w={220}
      searchable
      hidePickedOptions={false}
      styles={{ pillsList: { flexWrap: "nowrap", overflow: "hidden" } }}
      placeholder={localValue.length === 0 ? "Tags" : undefined}
      value={localValue}
      options={options}
      buildOption={(tag) => tag}
      onChange={(tags) => {
        dirty.current = true;
        setLocalValue(tags);
      }}
      onDropdownClose={() => commit(localValue)}
      renderPill={({ option, value: tag, onRemove }) => {
        const label = option?.label ?? tag ?? option?.value ?? "";
        const index = localValue.indexOf(String(tag ?? option?.value));
        if (index === MAX_VISIBLE_TAGS) {
          return <Pill>+{localValue.length - MAX_VISIBLE_TAGS}</Pill>;
        }
        if (index > MAX_VISIBLE_TAGS) {
          return null;
        }
        return (
          <Pill withRemoveButton onRemove={onRemove}>
            {label}
          </Pill>
        );
      }}
    />
  );
};

interface TriStateFilterProps {
  ariaLabel: string;
  trueLabel: string;
  falseLabel: string;
  value: boolean | undefined;
  onChange: (value: boolean | undefined) => void;
}

const TriStateFilter = ({
  ariaLabel,
  trueLabel,
  falseLabel,
  value,
  onChange,
}: TriStateFilterProps) => (
  <SegmentedControl
    size="sm"
    aria-label={ariaLabel}
    value={value === undefined ? "all" : value ? "true" : "false"}
    onChange={(v) => onChange(v === "all" ? undefined : v === "true")}
    data={[
      { value: "all", label: "All" },
      { value: "true", label: trueLabel },
      { value: "false", label: falseLabel },
    ]}
  ></SegmentedControl>
);

interface SortControlProps {
  query: Parameter.ListState;
  filterConfig: FilterConfig;
  setSort: (by: string, order: "asc" | "desc") => void;
}

const ItemViewSortControl = ({
  query,
  filterConfig,
  setSort,
}: SortControlProps) => {
  const sortBy = query.sortBy ?? filterConfig.sortFields[0]?.value ?? "title";
  const sortOrder = query.sortOrder ?? "asc";

  const sortLabel =
    filterConfig.sortFields.find((field) => field.value === sortBy)?.label ??
    sortBy;

  const handleSort = (field: string) => {
    if (field === sortBy) {
      setSort(sortBy, sortOrder === "asc" ? "desc" : "asc");
      return;
    }
    setSort(field, "asc");
  };

  return (
    <Menu position="bottom-end" shadow="md" withinPortal>
      <Menu.Target>
        <ToolboxIconButton
          icon={faSort}
          aria-label={`Sort: ${sortLabel}, ${sortOrder === "asc" ? "ascending" : "descending"}`}
        >
          Sort
        </ToolboxIconButton>
      </Menu.Target>
      <Menu.Dropdown>
        {filterConfig.sortFields.map((field) => (
          <Menu.Item
            key={field.value}
            onClick={() => handleSort(field.value)}
            rightSection={
              field.value === sortBy ? (
                <FontAwesomeIcon
                  icon={sortOrder === "asc" ? faCaretUp : faCaretDown}
                ></FontAwesomeIcon>
              ) : undefined
            }
          >
            {field.label}
          </Menu.Item>
        ))}
      </Menu.Dropdown>
    </Menu>
  );
};

// Filter and sort controls. Rendered as a fragment so the parent can lay them
// out inline (desktop) or stacked inside a popover (mobile).
const ItemViewFilterControls = ({
  query,
  filterConfig,
  tagOptions,
  setFilter,
}: FilterControlsProps) => {
  const { data: profiles } = useLanguageProfiles();
  const { data: languages } = useLanguages();

  const profileOptions = useMemo(
    () => [
      // 0 means "items without a languages profile" (sent as "none")
      { value: 0, label: "No profile" },
      ...(profiles ?? []).map((profile) => ({
        value: profile.profileId,
        label: profile.name,
      })),
    ],
    [profiles],
  );

  const audioOptions = useMemo(
    () =>
      (languages ?? []).map((language) => ({
        value: language.name,
        label: language.name,
      })),
    [languages],
  );

  return (
    <>
      {filterConfig.filters?.monitored && (
        <TriStateFilter
          ariaLabel="Monitored"
          trueLabel="Monitored"
          falseLabel="Unmonitored"
          value={query.filters?.monitored}
          onChange={(value) => setFilter("monitored", value)}
        />
      )}

      {filterConfig.filters?.missing && (
        <TriStateFilter
          ariaLabel="Missing subtitles"
          trueLabel="Missing"
          falseLabel="Complete"
          value={query.filters?.missing}
          onChange={(value) => setFilter("missing", value)}
        />
      )}

      {filterConfig.filters?.profile && (
        <Selector<number | null>
          size="sm"
          w={150}
          placeholder="Profile"
          clearable
          value={query.filters?.profileId ?? null}
          options={profileOptions}
          onChange={(value) =>
            setFilter("profileId", value === null ? undefined : value)
          }
        />
      )}

      {filterConfig.filters?.audio && (
        <Selector<string | null>
          size="sm"
          w={150}
          placeholder="Audio"
          clearable
          searchable
          value={query.filters?.audioLanguage ?? null}
          options={audioOptions}
          onChange={(value) =>
            setFilter("audioLanguage", value === null ? undefined : value)
          }
        />
      )}

      {filterConfig.filters?.tags && (
        <TagsFilterSelector
          value={query.filters?.tags ?? EMPTY_TAGS}
          options={tagOptions}
          onChange={(value) => setFilter("tags", value)}
        />
      )}
    </>
  );
};

interface ToolboxProps {
  totalCount: number;
  viewMode: ViewMode;
  canShowPoster: boolean;
  onViewModeChange: (mode: ViewMode) => void;
  query: Parameter.ListState;
  filterConfig: FilterConfig;
  useTags?: () => Pick<UseQueryResult<string[]>, "data">;
  setSort: (by: string, order: "asc" | "desc") => void;
  setFilter: SetFilter;
}

const ItemViewToolbox = ({
  totalCount,
  viewMode,
  canShowPoster,
  onViewModeChange,
  query,
  filterConfig,
  useTags = () => ({ data: undefined }),
  setSort,
  setFilter,
}: ToolboxProps) => {
  const navigate = useNavigate();
  const location = useLocation();
  const [filtersOpened, setFiltersOpened] = useState(false);

  // Collapse the inline filter controls into a popover button when they no
  // longer fit next to the Mass Edit button. Records the width at which the
  // controls overflowed so they only expand again when there is room.
  const [groupEl, setGroupEl] = useState<HTMLDivElement | null>(null);
  const [resizeRef, groupRect] = useResizeObserver();
  const groupRef = useMergedRef(setGroupEl, resizeRef);
  const controlsWidth = useRef(0);
  const [collapsed, setCollapsed] = useState(false);

  useEffect(() => {
    if (!groupEl) {
      return;
    }

    const epsilon = 8;
    if (!collapsed && groupEl.scrollWidth > groupEl.clientWidth + epsilon) {
      controlsWidth.current = groupEl.scrollWidth;
      setCollapsed(true);
      return;
    }
    if (collapsed && groupEl.clientWidth >= controlsWidth.current + epsilon) {
      setCollapsed(false);
    }
  }, [groupEl, groupRect, collapsed]);

  const activeFilterCount = Object.keys(query.filters ?? {}).length;

  const { data: allTags } = useTags();

  const tagOptions = useMemo(() => {
    const tags = new Set<string>(allTags ?? []);
    // allTags may lag behind a just-picked tag; keep active filters visible.
    query.filters?.tags?.forEach((tag) => tags.add(tag));
    return Array.from(tags)
      .sort()
      .map((tag) => ({ value: tag, label: tag }));
  }, [allTags, query.filters?.tags]);

  const controls = (
    <ItemViewFilterControls
      query={query}
      filterConfig={filterConfig}
      tagOptions={tagOptions}
      setFilter={setFilter}
    ></ItemViewFilterControls>
  );

  return (
    <Toolbox>
      <Group
        ref={groupRef}
        gap="sm"
        wrap="nowrap"
        align="center"
        flex={1}
        miw={0}
        preventGrowOverflow={false}
      >
        <ToolboxIconButton
          disabled={totalCount === 0}
          icon={faList}
          style={{ flexShrink: 0 }}
          onClick={() =>
            navigate({ pathname: "edit", search: location.search })
          }
        >
          Mass Edit
        </ToolboxIconButton>

        {!collapsed && (
          <Group
            gap="sm"
            wrap="nowrap"
            align="center"
            style={{ flexShrink: 0 }}
          >
            {controls}
          </Group>
        )}
      </Group>

      <Group gap="sm" wrap="nowrap" align="center">
        {viewMode === "poster" && (
          <ItemViewSortControl
            query={query}
            filterConfig={filterConfig}
            setSort={setSort}
          ></ItemViewSortControl>
        )}

        {canShowPoster && (
          <Menu position="bottom-end" shadow="md" withinPortal>
            <Menu.Target>
              <ToolboxIconButton
                icon={viewMode === "table" ? faTableList : faTableCellsLarge}
                aria-label={`View: ${viewMode}`}
              >
                View
              </ToolboxIconButton>
            </Menu.Target>
            <Menu.Dropdown>
              <Menu.Item
                leftSection={
                  <FontAwesomeIcon icon={faTableList}></FontAwesomeIcon>
                }
                rightSection={
                  viewMode === "table" ? (
                    <FontAwesomeIcon icon={faCheck}></FontAwesomeIcon>
                  ) : undefined
                }
                onClick={() => onViewModeChange("table")}
              >
                Table view
              </Menu.Item>
              <Menu.Item
                leftSection={
                  <FontAwesomeIcon icon={faTableCellsLarge}></FontAwesomeIcon>
                }
                rightSection={
                  viewMode === "poster" ? (
                    <FontAwesomeIcon icon={faCheck}></FontAwesomeIcon>
                  ) : undefined
                }
                onClick={() => onViewModeChange("poster")}
              >
                Poster view
              </Menu.Item>
            </Menu.Dropdown>
          </Menu>
        )}

        {collapsed && (
          <Popover
            opened={filtersOpened}
            onChange={setFiltersOpened}
            position="bottom-end"
            withArrow
            shadow="md"
            withinPortal
          >
            <Popover.Target>
              <Indicator
                disabled={activeFilterCount === 0}
                label={activeFilterCount}
                size={16}
              >
                <ToolboxIconButton
                  icon={faFilter}
                  aria-label="Filters"
                  onClick={() => setFiltersOpened((opened) => !opened)}
                >
                  Filters
                </ToolboxIconButton>
              </Indicator>
            </Popover.Target>
            <Popover.Dropdown>
              <Stack gap="xs" w={260}>
                {controls}
              </Stack>
            </Popover.Dropdown>
          </Popover>
        )}
      </Group>
    </Toolbox>
  );
};

interface ViewProps<T extends Item.Base> {
  queryKey: QueryKey;
  queryFn: RangeQuery<T>;
  query: Parameter.ListState;
  toolbox: Omit<ToolboxProps, "totalCount">;
}

const ItemTableView = <T extends Item.Base>({
  queryKey,
  queryFn,
  query,
  columns,
  toolbox,
}: ViewProps<T> & { columns: ColumnDef<T>[] }) => {
  const tableQuery = usePaginationQuery(queryKey, queryFn, true, query);
  const { filterConfig, setSort } = toolbox;

  const sortableIds = useMemo(
    () => new Set(filterConfig.sortFields.map((field) => field.value)),
    [filterConfig],
  );

  const headersRenderer = useCallback(
    (headers: Header<T, unknown>[]) =>
      headers.map((header) => {
        const id = header.column.id;
        const isSortable = sortableIds.has(id);
        const isSorted = query.sortBy === id;
        const order = query.sortOrder ?? "asc";

        return (
          <Table.Th
            key={header.id}
            style={{
              whiteSpace: "nowrap",
              cursor: isSortable ? "pointer" : undefined,
            }}
            onClick={() => {
              if (!isSortable) {
                return;
              }
              setSort(id, isSorted && order === "asc" ? "desc" : "asc");
            }}
          >
            <Group gap="xs" wrap="nowrap" align="center">
              {flexRender(header.column.columnDef.header, header.getContext())}
              {isSortable && (
                <FontAwesomeIcon
                  icon={
                    isSorted
                      ? order === "asc"
                        ? faCaretUp
                        : faCaretDown
                      : faSort
                  }
                ></FontAwesomeIcon>
              )}
            </Group>
          </Table.Th>
        );
      }),
    [sortableIds, query, setSort],
  );

  return (
    <>
      <ItemViewToolbox
        {...toolbox}
        totalCount={tableQuery.paginationStatus.totalCount}
      ></ItemViewToolbox>
      <QueryPageTable
        columns={columns}
        query={tableQuery}
        tableStyles={{ emptyText: "No items found", headersRenderer }}
      ></QueryPageTable>
    </>
  );
};

const ItemPosterView = <T extends Item.Base>({
  queryKey,
  queryFn,
  query,
  renderPoster,
  toolbox,
}: ViewProps<T> & { renderPoster: (item: T) => ReactNode }) => {
  const posterQuery = useInfinitePaginationQuery(
    queryKey,
    queryFn,
    true,
    query,
  );

  return (
    <>
      <ItemViewToolbox
        {...toolbox}
        totalCount={posterQuery.paginationStatus.totalCount}
      ></ItemViewToolbox>
      <QueryPosterGrid
        query={posterQuery}
        renderPoster={renderPoster}
        emptyText="No items found"
      ></QueryPosterGrid>
    </>
  );
};

const ItemView = <T extends Item.Base>({
  queryKey,
  queryFn,
  columns,
  viewModeKey,
  renderPoster,
  filterConfig,
  useTags,
  statePrefix,
}: Props<T>) => {
  const [viewMode, setViewMode] = useViewMode(viewModeKey ?? "item-view-mode");
  const { query, setSort, setFilter } = useListQueryState(statePrefix);

  const canShowPoster = viewModeKey !== undefined && renderPoster !== undefined;
  const showPoster = canShowPoster && viewMode === "poster";

  const toolbox: Omit<ToolboxProps, "totalCount"> = {
    viewMode,
    canShowPoster,
    onViewModeChange: setViewMode,
    query,
    filterConfig,
    useTags,
    setSort,
    setFilter,
  };

  // Only one view is mounted at a time, keeping a single active query. Each
  // view owns its query hook and renders the toolbox with its total count.
  if (showPoster && renderPoster) {
    return (
      <ItemPosterView
        queryKey={queryKey}
        queryFn={queryFn}
        query={query}
        renderPoster={renderPoster}
        toolbox={toolbox}
      ></ItemPosterView>
    );
  }

  return (
    <ItemTableView
      queryKey={queryKey}
      queryFn={queryFn}
      query={query}
      columns={columns}
      toolbox={toolbox}
    ></ItemTableView>
  );
};

export default ItemView;
