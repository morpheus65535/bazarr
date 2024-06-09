import {
  UseColumnOrderInstanceProps,
  UseColumnOrderState,
  UseExpandedHooks,
  UseExpandedInstanceProps,
  UseExpandedOptions,
  UseExpandedRowProps,
  UseExpandedState,
  UseFiltersColumnOptions,
  UseFiltersColumnProps,
  UseGroupByCellProps,
  UseGroupByColumnOptions,
  UseGroupByColumnProps,
  UseGroupByHooks,
  UseGroupByInstanceProps,
  UseGroupByOptions,
  UseGroupByRowProps,
  UseGroupByState,
  UsePaginationInstanceProps,
  UsePaginationOptions,
  UsePaginationState,
  UseRowSelectHooks,
  UseRowSelectInstanceProps,
  UseRowSelectOptions,
  UseRowSelectRowProps,
  UseRowSelectState,
  UseSortByColumnOptions,
  UseSortByColumnProps,
  UseSortByHooks,
  UseSortByInstanceProps,
  UseSortByOptions,
  UseSortByState,
} from "react-table";
import {} from "@/components/tables/plugins";

declare module "react-table" {
  // take this file as-is, or comment out the sections that don't apply to your plugin configuration

  interface useSelectionProps<D extends Record<string, unknown>> {
    onSelect?: (items: D[]) => void;
    canSelect?: (item: D) => boolean;
  }

  // eslint-disable-next-line @typescript-eslint/no-empty-interface
  interface CustomTableProps<D extends Record<string, unknown>>
    extends useSelectionProps<D> {}

  export interface TableOptions<D extends Record<string, unknown>>
    extends UseExpandedOptions<D>,
      // UseFiltersOptions<D>,
      // UseGlobalFiltersOptions<D>,
      UseGroupByOptions<D>,
      UsePaginationOptions<D>,
      // UseResizeColumnsOptions<D>,
      UseRowSelectOptions<D>,
      // UseRowStateOptions<D>,
      UseSortByOptions<D>,
      CustomTableProps<D> {
    data: readonly D[];
  }

  export interface Hooks<
    D extends Record<string, unknown> = Record<string, unknown>,
  > extends UseExpandedHooks<D>,
      UseGroupByHooks<D>,
      UseRowSelectHooks<D>,
      UseSortByHooks<D> {}

  export interface TableInstance<
    D extends Record<string, unknown> = Record<string, unknown>,
  > extends UseColumnOrderInstanceProps<D>,
      UseExpandedInstanceProps<D>,
      // UseFiltersInstanceProps<D>,
      // UseGlobalFiltersInstanceProps<D>,
      UseGroupByInstanceProps<D>,
      UsePaginationInstanceProps<D>,
      UseRowSelectInstanceProps<D>,
      // UseRowStateInstanceProps<D>,
      UseSortByInstanceProps<D>,
      CustomTableProps<D> {}

  export interface TableState<
    D extends Record<string, unknown> = Record<string, unknown>,
  > extends UseColumnOrderState<D>,
      UseExpandedState<D>,
      // UseFiltersState<D>,
      // UseGlobalFiltersState<D>,
      UseGroupByState<D>,
      UsePaginationState<D>,
      // UseResizeColumnsState<D>,
      UseRowSelectState<D>,
      // UseRowStateState<D>,
      UseSortByState<D> {}

  export interface ColumnInterface<
    D extends Record<string, unknown> = Record<string, unknown>,
  > extends UseFiltersColumnOptions<D>,
      // UseGlobalFiltersColumnOptions<D>,
      UseGroupByColumnOptions<D>,
      // UseResizeColumnsColumnOptions<D>,
      UseSortByColumnOptions<D> {}

  export interface ColumnInstance<
    D extends Record<string, unknown> = Record<string, unknown>,
  > extends UseFiltersColumnProps<D>,
      UseGroupByColumnProps<D>,
      // UseResizeColumnsColumnProps<D>,
      UseSortByColumnProps<D> {}

  // eslint-disable-next-line @typescript-eslint/no-empty-interface
  export interface Cell<
    D extends Record<string, unknown> = Record<string, unknown>,
  > extends UseGroupByCellProps<D> {}

  export interface Row<
    D extends Record<string, unknown> = Record<string, unknown>,
  > extends UseExpandedRowProps<D>,
      UseGroupByRowProps<D>,
      UseRowSelectRowProps<D> {}
}
