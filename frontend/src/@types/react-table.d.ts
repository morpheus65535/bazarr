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
import {} from "../components/tables/plugins";
import { PageControlAction } from "../components/tables/types";

declare module "react-table" {
  // take this file as-is, or comment out the sections that don't apply to your plugin configuration

  // Customize of React Table
  type TableUpdater<D extends object> = (row: Row<D>, ...others: any[]) => void;

  interface useAsyncPaginationProps<D extends Record<string, unknown>> {
    loader?: (start: number, length: number) => void;
    idState?: AsyncState<OrderIdState<D>>;
    idGetter?: (item: D) => number;
  }

  interface useAsyncPaginationState<D extends Record<string, unknown>> {
    loading?: PageControlAction;
  }

  interface useSelectionProps<D extends Record<string, unknown>> {
    select?: boolean;
    onSelect?: (items: D[]) => void;
  }

  interface useSelectionState<D extends Record<string, unknown>> {}

  interface CustomTableProps<D extends Record<string, unknown>>
    extends useSelectionProps<D>,
      useAsyncPaginationProps<D> {
    update?: TableUpdater<D>;
    loose?: any[];
  }

  interface CustomTableState<D extends Record<string, unknown>>
    extends useSelectionState<D>,
      useAsyncPaginationState<D> {}

  export interface TableOptions<
    D extends Record<string, unknown>
  > extends UseExpandedOptions<D>,
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
    D extends Record<string, unknown> = Record<string, unknown>
  > extends UseExpandedHooks<D>,
      UseGroupByHooks<D>,
      UseRowSelectHooks<D>,
      UseSortByHooks<D> {}

  export interface TableInstance<
    D extends Record<string, unknown> = Record<string, unknown>
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
    D extends Record<string, unknown> = Record<string, unknown>
  > extends UseColumnOrderState<D>,
      UseExpandedState<D>,
      // UseFiltersState<D>,
      // UseGlobalFiltersState<D>,
      UseGroupByState<D>,
      UsePaginationState<D>,
      // UseResizeColumnsState<D>,
      UseRowSelectState<D>,
      // UseRowStateState<D>,
      UseSortByState<D>,
      CustomTableState<D> {}

  export interface ColumnInterface<
    D extends Record<string, unknown> = Record<string, unknown>
  > extends UseFiltersColumnOptions<D>,
      // UseGlobalFiltersColumnOptions<D>,
      UseGroupByColumnOptions<D>,
      // UseResizeColumnsColumnOptions<D>,
      UseSortByColumnOptions<D> {
    selectHide?: boolean;
    className?: string;
  }

  export interface ColumnInstance<
    D extends Record<string, unknown> = Record<string, unknown>
  > extends UseFiltersColumnProps<D>,
      UseGroupByColumnProps<D>,
      // UseResizeColumnsColumnProps<D>,
      UseSortByColumnProps<D> {}

  export interface Cell<
    D extends Record<string, unknown> = Record<string, unknown>,
    V = any
  > extends UseGroupByCellProps<D> {}

  export interface Row<
    D extends Record<string, unknown> = Record<string, unknown>
  > extends UseExpandedRowProps<D>,
      UseGroupByRowProps<D>,
      UseRowSelectRowProps<D> {}
}
