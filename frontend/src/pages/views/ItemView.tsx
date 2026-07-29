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
import { ColumnDef } from "@tanstack/react-table";
import { UsePaginationQueryResult } from "@/apis/queries/hooks";
import { QueryPageTable, QueryPosterGrid, Toolbox } from "@/components";
import { useViewMode, ViewMode } from "@/utilities/viewMode";

interface Props<T extends Item.Base = Item.Base> {
  query: UsePaginationQueryResult<T>;
  columns: ColumnDef<T>[];
  // Enables the table/poster toggle when both are provided. The key is used
  // to persist the selection in the browser.
  viewModeKey?: string;
  renderPoster?: (item: T) => ReactNode;
}

function ItemView<T extends Item.Base>({
  query,
  columns,
  viewModeKey,
  renderPoster,
}: Props<T>) {
  const navigate = useNavigate();

  const [viewMode, setViewMode] = useViewMode(viewModeKey ?? "item-view-mode");

  const canShowPoster = viewModeKey !== undefined && renderPoster !== undefined;
  const showPoster = canShowPoster && viewMode === "poster";

  return (
    <>
      <Toolbox>
        <Toolbox.Button
          disabled={query.paginationStatus.totalCount === 0}
          icon={faList}
          onClick={() => navigate("edit")}
        >
          Mass Edit
        </Toolbox.Button>
        {canShowPoster && (
          <SegmentedControl
            size="xs"
            value={viewMode}
            onChange={(value) => setViewMode(value as ViewMode)}
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
                      <FontAwesomeIcon
                        icon={faTableCellsLarge}
                      ></FontAwesomeIcon>
                      <VisuallyHidden>Poster view</VisuallyHidden>
                    </Center>
                  </Tooltip>
                ),
              },
            ]}
          ></SegmentedControl>
        )}
      </Toolbox>
      {showPoster && renderPoster ? (
        <QueryPosterGrid
          query={query}
          renderPoster={renderPoster}
          emptyText="No items found"
        ></QueryPosterGrid>
      ) : (
        <QueryPageTable
          columns={columns}
          query={query}
          tableStyles={{ emptyText: "No items found" }}
        ></QueryPageTable>
      )}
    </>
  );
}

export default ItemView;
