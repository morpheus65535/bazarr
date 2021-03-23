import { isNull } from "lodash";
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
import { isNonNullable } from "../../../utilites";
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
  if (action.type === ActionLoadingChange && instance) {
    let pageToLoad:
      | PageControlAction
      | undefined = action.pageToLoad as PageControlAction;
    let needLoadingScreen = false;
    const { asyncState } = instance;
    const { pageIndex, pageSize } = state;
    let index = pageIndex;
    if (pageToLoad === "prev") {
      index -= 1;
    } else if (pageToLoad === "next") {
      index += 1;
    } else if (typeof pageToLoad === "number") {
      index = pageToLoad;
    }
    const pageStart = index * pageSize;
    const pageEnd = pageStart + pageSize;
    if (asyncState) {
      const error = asyncState.error;
      const order = asyncState.data.order.slice(pageStart, pageEnd);

      const isInitializedError = order.length === 0 && error !== undefined;
      const isLoadingError = order.length !== 0 && order.every(isNull);

      if (isInitializedError || isLoadingError) {
        needLoadingScreen = true;
      } else if (order.every(isNonNullable)) {
        pageToLoad = undefined;
      }
    }
    return { ...state, pageToLoad, needLoadingScreen };
  }
  return state;
}

function useOptions<T extends object>(options: TableOptions<T>) {
  options.manualPagination = true;
  if (options.initialState === undefined) {
    options.initialState = {};
  }
  options.initialState.pageToLoad = 0;
  options.initialState.needLoadingScreen = true;
  return options;
}

function useInstance<T extends object>(instance: TableInstance<T>) {
  const {
    plugins,
    asyncLoader,
    dispatch,
    asyncState,
    asyncId,
    rows,
    nextPage,
    previousPage,
    gotoPage,
    state: { pageIndex, pageSize, pageToLoad },
  } = instance;

  ensurePluginOrder(plugins, ["usePagination"], pluginName);

  const totalCount = asyncState?.data.order.length ?? 0;
  const pageCount = Math.ceil(totalCount / pageSize);
  const pageStart = pageIndex * pageSize;
  const pageEnd = pageStart + pageSize;

  useEffect(() => {
    // TODO Lazy Load
    if (pageToLoad === undefined) {
      return;
    }
    asyncLoader && asyncLoader(pageStart, pageSize);
  }, [asyncLoader, pageStart, pageSize, pageToLoad]);

  const setPageToLoad = useCallback(
    (pageToLoad?: PageControlAction) => {
      dispatch({ type: ActionLoadingChange, pageToLoad });
    },
    [dispatch]
  );

  useEffect(() => {
    if (asyncState?.updating === false) {
      setPageToLoad();
    }
  }, [asyncState?.updating, setPageToLoad]);

  const newGoto = useCallback(
    (updater: number | ((pageIndex: number) => number)) => {
      let page: number;
      if (typeof updater === "number") {
        page = updater;
      } else {
        page = updater(pageIndex);
      }
      if (page === pageIndex) {
        return;
      }
      setPageToLoad(page);
      gotoPage(page);
    },
    [pageIndex, setPageToLoad, gotoPage]
  );

  const newPrevious = useCallback(() => {
    if (pageIndex === 0) {
      return;
    }
    setPageToLoad("prev");
    previousPage();
  }, [setPageToLoad, previousPage, pageIndex]);

  const newNext = useCallback(() => {
    if (pageIndex === pageCount) {
      return;
    }
    setPageToLoad("next");
    nextPage();
  }, [setPageToLoad, nextPage, pageCount, pageIndex]);

  const newPages = useMemo(() => {
    // TODO: Performance

    const order = (asyncState?.data.order
      .slice(pageStart, pageEnd)
      .filter(isNonNullable) ?? []) as number[];

    return order.flatMap((num) => {
      const row = rows.find((v) => asyncId && asyncId(v.original) === num);
      if (row) {
        return [row];
      } else {
        return [];
      }
    });
  }, [pageStart, pageEnd, asyncId, asyncState?.data.order, rows]);

  Object.assign<TableInstance<T>, Partial<TableInstance<T>>>(instance, {
    previousPage: newPrevious,
    nextPage: newNext,
    gotoPage: newGoto,
    page: newPages,
    pageCount,
  });
}

export default useAsyncPagination;
