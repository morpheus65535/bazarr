import { ReactNode } from "react";
import { useNavigate } from "react-router";
import {
  Center,
  SegmentedControl,
  Tooltip,
  VisuallyHidden,
} from "@mantine/core";
import {
  faList,
  faTableCellsLarge,
  faTableList,
} from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { QueryKey } from "@tanstack/react-query";
import {
  useInfinitePaginationQuery,
  usePaginationQuery,
} from "@/apis/queries/hooks";
import { QueryPageTable, QueryPosterGrid, Toolbox } from "@/components";
import { AppColumnDef as ColumnDef } from "@/components/tables/features";
import { useViewMode, ViewMode } from "@/utilities/viewMode";

interface Props<T extends Item.Base = Item.Base> {
  queryKey: QueryKey;
  queryFn: RangeQuery<T>;
  columns: ColumnDef<T>[];
  // Enables the table/poster toggle when both are provided. The key is used
  // to persist the selection in the browser.
  viewModeKey?: string;
  renderPoster?: (item: T) => ReactNode;
}

interface ToolboxProps {
  totalCount: number;
  viewMode: ViewMode;
  canShowPoster: boolean;
  onViewModeChange: (mode: ViewMode) => void;
}

const ItemViewToolbox = ({
  totalCount,
  viewMode,
  canShowPoster,
  onViewModeChange,
}: ToolboxProps) => {
  const navigate = useNavigate();

  return (
    <Toolbox>
      <Toolbox.Button
        disabled={totalCount === 0}
        icon={faList}
        onClick={() => navigate("edit")}
      >
        Mass Edit
      </Toolbox.Button>
      {canShowPoster && (
        <SegmentedControl
          size="xs"
          value={viewMode}
          onChange={(value) => onViewModeChange(value as ViewMode)}
          data={[
            {
              value: "table",
              label: (
                <Tooltip label="Table view" openDelay={500}>
                  <Center component="span" style={{ display: "inline-flex" }}>
                    <FontAwesomeIcon icon={faTableList}></FontAwesomeIcon>
                    <VisuallyHidden>Table view</VisuallyHidden>
                  </Center>
                </Tooltip>
              ),
            },
            {
              value: "poster",
              label: (
                <Tooltip label="Poster view" openDelay={500}>
                  <Center component="span" style={{ display: "inline-flex" }}>
                    <FontAwesomeIcon icon={faTableCellsLarge}></FontAwesomeIcon>
                    <VisuallyHidden>Poster view</VisuallyHidden>
                  </Center>
                </Tooltip>
              ),
            },
          ]}
        ></SegmentedControl>
      )}
    </Toolbox>
  );
};

interface ViewProps<T extends Item.Base> {
  queryKey: QueryKey;
  queryFn: RangeQuery<T>;
  toolbox: Omit<ToolboxProps, "totalCount">;
}

const ItemTableView = <T extends Item.Base>({
  queryKey,
  queryFn,
  columns,
  toolbox,
}: ViewProps<T> & { columns: ColumnDef<T>[] }) => {
  const query = usePaginationQuery(queryKey, queryFn);

  return (
    <>
      <ItemViewToolbox
        {...toolbox}
        totalCount={query.paginationStatus.totalCount}
      ></ItemViewToolbox>
      <QueryPageTable
        columns={columns}
        query={query}
        tableStyles={{ emptyText: "No items found" }}
      ></QueryPageTable>
    </>
  );
};

const ItemPosterView = <T extends Item.Base>({
  queryKey,
  queryFn,
  renderPoster,
  toolbox,
}: ViewProps<T> & { renderPoster: (item: T) => ReactNode }) => {
  const query = useInfinitePaginationQuery(queryKey, queryFn);

  return (
    <>
      <ItemViewToolbox
        {...toolbox}
        totalCount={query.paginationStatus.totalCount}
      ></ItemViewToolbox>
      <QueryPosterGrid
        query={query}
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
}: Props<T>) => {
  const [viewMode, setViewMode] = useViewMode(viewModeKey ?? "item-view-mode");

  const canShowPoster = viewModeKey !== undefined && renderPoster !== undefined;
  const showPoster = canShowPoster && viewMode === "poster";

  const toolbox: ViewProps<T>["toolbox"] = {
    viewMode,
    canShowPoster,
    onViewModeChange: setViewMode,
  };

  // Only one view is mounted at a time, keeping a single active query. Each
  // view owns its query hook and renders the toolbox with its total count.
  if (showPoster && renderPoster) {
    return (
      <ItemPosterView
        queryKey={queryKey}
        queryFn={queryFn}
        renderPoster={renderPoster}
        toolbox={toolbox}
      ></ItemPosterView>
    );
  }

  return (
    <ItemTableView
      queryKey={queryKey}
      queryFn={queryFn}
      columns={columns}
      toolbox={toolbox}
    ></ItemTableView>
  );
};

export default ItemView;
