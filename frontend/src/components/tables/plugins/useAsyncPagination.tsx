import { isNumber } from "lodash";
import { useCallback, useEffect, useMemo } from "react";
import {
  ActionType,
  ensurePluginOrder,
  Hooks,
  ReducerTableState,
  TableInstance,
  TableOptions,
  TableState,
} from "react-table";
import { isNullable } from "../../../utilites";
import { PageControlAction } from "../types";

const pluginName = "useAsyncPagination";

const ActionLoadingChange = "loading-change";

function useAsyncPagination<T extends object>(hooks: Hooks<T>) {
  hooks.stateReducers.push(reducer);
  hooks.useInstance.push(useInstance);
  hooks.useOptions.push(useOptions);
}
useAsyncPagination.pluginName = pluginName;

function reducer<T extends object>(
  state: TableState<T>,
  action: ActionType,
  previous: TableState<T> | undefined,
  instance: TableInstance<T> | undefined
): ReducerTableState<T> {
  if (action.type === ActionLoadingChange) {
    const loading = action.loading;
    return { ...state, loading };
  }
  return state;
}

function useOptions<T extends object>(options: TableOptions<T>) {
  options.manualPagination = true;
  return options;
}

function useInstance<T extends object>(instance: TableInstance<T>) {
  const {
    plugins,
    loader,
    dispatch,
    idState,
    idGetter,
    rows,
    nextPage,
    previousPage,
    gotoPage,
    state: { pageIndex, pageSize, loading },
  } = instance;

  ensurePluginOrder(plugins, ["usePagination"], pluginName);

  const totalCount = idState?.data.order.length ?? 0;

  const pageStart = pageSize * pageIndex;
  const pageEnd = pageStart + pageSize;
  const pageCount = Math.ceil(totalCount / pageSize);

  useEffect(() => {
    // TODO Lazy Load
    let start = pageStart;
    let size = pageSize;
    if (loading === "next") {
      start += size;
    } else if (loading === "prev") {
      start = Math.max(0, start - size);
    } else if (isNumber(loading)) {
      start = loading * pageSize;
    }
    loader && loader(start, pageSize);
  }, [loader, pageStart, pageSize, loading]);

  const updateLoading = useCallback(
    (state?: PageControlAction) => {
      dispatch({ type: ActionLoadingChange, loading: state });
    },
    [dispatch]
  );

  useEffect(() => {
    if (idState?.updating === false) {
      updateLoading();
    }
  }, [idState?.updating, updateLoading]);

  const newGoto = useCallback(
    (updater: number | ((pageIndex: number) => number)) => {
      let page: number;
      if (typeof updater === "number") {
        page = updater;
      } else {
        page = updater(pageIndex);
      }
      updateLoading(page);
      gotoPage(page);
    },
    [pageIndex, updateLoading, gotoPage]
  );

  const newPrevious = useCallback(() => {
    updateLoading("prev");
    previousPage();
  }, [updateLoading, previousPage]);

  const newNext = useCallback(() => {
    updateLoading("next");
    nextPage();
  }, [updateLoading, nextPage]);

  const newPages = useMemo(() => {
    // TODO: Performance
    const order = (idState?.data.order
      .slice(pageStart, pageEnd)
      .filter((v) => !isNullable(v)) ?? []) as number[];

    return order.flatMap((num) => {
      const row = rows.find((v) => idGetter && idGetter(v.original) === num);
      if (row) {
        return [row];
      } else {
        return [];
      }
    });
  }, [pageStart, pageEnd, idGetter, idState?.data.order, rows]);

  Object.assign<TableInstance<T>, Partial<TableInstance<T>>>(instance, {
    previousPage: newPrevious,
    nextPage: newNext,
    gotoPage: newGoto,
    page: newPages,
    pageCount,
  });
}

export default useAsyncPagination;
