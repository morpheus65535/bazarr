import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useSearchParams } from "react-router";
import {
  InfiniteData,
  QueryKey,
  useInfiniteQuery,
  UseInfiniteQueryResult,
  useQuery,
  useQueryClient,
  UseQueryResult,
} from "@tanstack/react-query";
import { GetItemId, useOnValueChange } from "@/utilities";
import { usePageSize } from "@/utilities/storage";
import { QueryKeys } from "./keys";

export type UsePaginationQueryResult<T extends object> = UseQueryResult<
  DataWrapperWithTotal<T>
> & {
  controls: {
    gotoPage: (index: number) => void;
  };
  paginationStatus: {
    isPageLoading: boolean;
    totalCount: number;
    pageSize: number;
    pageCount: number;
    page: number;
  };
};

export const usePaginationQuery = <
  TObject extends object = object,
  TQueryKey extends QueryKey = QueryKey,
>(
  queryKey: TQueryKey,
  queryFn: RangeQuery<TObject>,
  cacheIndividual = true,
  query: Parameter.ListState = {},
): UsePaginationQueryResult<TObject> => {
  const client = useQueryClient();

  const [searchParams] = useSearchParams();

  const [page, setIndex] = useState(
    searchParams.get("page") ? Number(searchParams.get("page")) - 1 : 0,
  );

  const queryKeySuffix = useMemo(() => JSON.stringify(query), [query]);

  const pageSize = usePageSize();

  const start = page * pageSize;

  const results = useQuery({
    queryKey: [...queryKey, QueryKeys.Range, { start, size: pageSize, query }],

    queryFn: () => {
      const param: Parameter.ListQuery = {
        start,
        length: pageSize,
        ...query,
      };
      return queryFn(param);
    },
  });

  const { data } = results;

  useEffect(() => {
    if (results.isSuccess && results.data && cacheIndividual) {
      results.data.data.forEach((item) => {
        const id = GetItemId(item);
        if (id) {
          client.setQueryData([...queryKey, id], item);
        }
      });
    }
  }, [
    results.isSuccess,
    results.data,
    client,
    cacheIndividual,
    queryKey,
    page,
    query,
  ]);

  const totalCount = data?.total ?? 0;
  const pageCount = Math.ceil(totalCount / pageSize);

  const gotoPage = useCallback(
    (idx: number) => {
      if (idx >= 0 && idx < pageCount) {
        setIndex(idx);
      }
    },
    [pageCount],
  );

  const [isPageLoading, setIsPageLoading] = useState(false);

  useOnValueChange(page, () => {
    if (results.isFetching) {
      setIsPageLoading(true);
    }
  });

  useEffect(() => {
    if (!results.isFetching) {
      setIsPageLoading(false);
    }
  }, [results.isFetching]);

  // Reset to the first page when the filter/sort query changes. The ref skips
  // the effect on mount so a ?page= URL param is still honored on first load
  // (useOnValueChange cannot be used here, it fires on mount).
  const hasResetOnQueryChange = useRef(false);
  useEffect(() => {
    if (hasResetOnQueryChange.current) {
      setIndex(0);
      return;
    }
    hasResetOnQueryChange.current = true;
  }, [queryKeySuffix]);

  // Reset page index if we out of bound
  useEffect(() => {
    if (pageCount === 0) return;

    if (page >= pageCount) {
      setIndex(pageCount - 1);
      return;
    }
    if (page < 0) {
      setIndex(0);
    }
  }, [page, pageCount]);

  return {
    ...results,
    paginationStatus: {
      isPageLoading,
      totalCount,
      pageCount,
      pageSize,
      page,
    },
    controls: {
      gotoPage,
    },
  };
};

export type UseInfinitePaginationQueryResult<T extends object> = Omit<
  UseInfiniteQueryResult<InfiniteData<DataWrapperWithTotal<T>, number>>,
  "fetchNextPage"
> & {
  items: T[];
  controls: {
    fetchNextPage: () => void;
  };
  paginationStatus: {
    isInitialLoading: boolean;
    isFetchingNextPage: boolean;
    hasNextPage: boolean;
    totalCount: number;
    pageSize: number;
  };
};

// Accumulates range queries into a single growing list for infinite scroll.
// Shares the QueryKeys.Range prefix with usePaginationQuery so prefix-based
// invalidation (e.g. [QueryKeys.Movies]) refetches all loaded pages.
export const useInfinitePaginationQuery = <
  TObject extends object = object,
  TQueryKey extends QueryKey = QueryKey,
>(
  queryKey: TQueryKey,
  queryFn: RangeQuery<TObject>,
  cacheIndividual = true,
  query: Parameter.ListState = {},
): UseInfinitePaginationQueryResult<TObject> => {
  const client = useQueryClient();

  const pageSize = usePageSize();

  const results = useInfiniteQuery<
    DataWrapperWithTotal<TObject>,
    Error,
    InfiniteData<DataWrapperWithTotal<TObject>, number>,
    QueryKey,
    number
  >({
    queryKey: [...queryKey, QueryKeys.Range, { size: pageSize, query }],

    queryFn: ({ pageParam }) => {
      const param: Parameter.ListQuery = {
        start: pageParam,
        length: pageSize,
        ...query,
      };
      return queryFn(param);
    },

    initialPageParam: 0,

    getNextPageParam: (lastPage, allPages) => {
      const fetched = allPages.length * pageSize;
      return fetched < lastPage.total ? fetched : undefined;
    },
  });

  const { data } = results;

  useEffect(() => {
    if (results.isSuccess && data && cacheIndividual) {
      data.pages.forEach((page) => {
        page.data.forEach((item) => {
          const id = GetItemId(item);
          if (id) {
            client.setQueryData([...queryKey, id], item);
          }
        });
      });
    }
  }, [results.isSuccess, data, client, cacheIndividual, queryKey, query]);

  const { fetchNextPage: fetchNext, ...rest } = results;
  const { hasNextPage, isFetchingNextPage } = results;

  const fetchNextPage = useCallback(() => {
    if (hasNextPage && !isFetchingNextPage) {
      void fetchNext();
    }
  }, [hasNextPage, isFetchingNextPage, fetchNext]);

  const items = useMemo(
    () => data?.pages.flatMap((page) => page.data) ?? [],
    [data],
  );
  const totalCount = data?.pages[data.pages.length - 1]?.total ?? 0;

  // Spread omits the raw fetchNextPage so controls.fetchNextPage is the only
  // paging entry point, matching usePaginationQuery's controls shape
  return {
    ...rest,
    items,
    paginationStatus: {
      isInitialLoading: results.isLoading,
      isFetchingNextPage,
      hasNextPage,
      totalCount,
      pageSize,
    },
    controls: {
      fetchNextPage,
    },
  };
};
