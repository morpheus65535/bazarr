import {
  aggregationFns,
  Cell,
  ColumnDef,
  columnFilteringFeature,
  columnGroupingFeature,
  columnVisibilityFeature,
  createExpandedRowModel,
  createFilteredRowModel,
  createGroupedRowModel,
  createPaginatedRowModel,
  createSortedRowModel,
  filterFns,
  globalFilteringFeature,
  Header,
  Row,
  rowAggregationFeature,
  RowData,
  rowExpandingFeature,
  rowPaginationFeature,
  rowSelectionFeature,
  rowSortingFeature,
  sortFns,
  Table,
  tableFeatures,
  TableOptions,
} from "@tanstack/react-table";

// Shared feature set for all app tables. Row models and fns are registered
// here so individual tables only declare data/columns and behavior options.
export const appTableFeatures = tableFeatures({
  rowSelectionFeature,
  rowExpandingFeature,
  rowSortingFeature,
  rowAggregationFeature,
  columnGroupingFeature,
  columnVisibilityFeature,
  columnFilteringFeature,
  globalFilteringFeature,
  rowPaginationFeature,
  expandedRowModel: createExpandedRowModel(),
  groupedRowModel: createGroupedRowModel(),
  filteredRowModel: createFilteredRowModel(),
  sortedRowModel: createSortedRowModel(),
  paginatedRowModel: createPaginatedRowModel(),
  filterFns,
  sortFns,
  aggregationFns,
});

export type AppTableFeatures = typeof appTableFeatures;

export type { RowData };

export type AppColumnDef<TData extends RowData, TValue = unknown> = ColumnDef<
  AppTableFeatures,
  TData,
  TValue
>;

export type AppTable<TData extends RowData> = Table<AppTableFeatures, TData>;

export type AppTableOptions<TData extends RowData> = TableOptions<
  AppTableFeatures,
  TData
>;

export type AppRow<TData extends RowData> = Row<AppTableFeatures, TData>;

export type AppHeader<TData extends RowData, TValue = unknown> = Header<
  AppTableFeatures,
  TData,
  TValue
>;

export type AppCell<TData extends RowData, TValue = unknown> = Cell<
  AppTableFeatures,
  TData,
  TValue
>;
