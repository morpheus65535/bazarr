import { useCallback, useEffect, useState } from "react";
import {
  QueryKey,
  useQuery,
  useQueryClient,
  UseQueryResult,
} from "react-query";
import { GetItemId } from "utilities";
import { usePageSize } from "utilities/storage";
import { QueryKeys } from "./keys";

export type PaginationQuery<T extends object> = UseQueryResult<
  DataWrapperWithTotal<T>
> & {
  controls: {
    previousPage: () => void;
    nextPage: () => void;
    gotoPage: (index: number) => void;
  };
  paginationStatus: {
    totalCount: number;
    pageSize: number;
    pageCount: number;
    page: number;
    canPrevious: boolean;
    canNext: boolean;
  };
};

export function usePaginationQuery<
  TObject extends object = object,
  TQueryKey extends QueryKey = QueryKey
>(queryKey: TQueryKey, queryFn: RangeQuery<TObject>): PaginationQuery<TObject> {
  const client = useQueryClient();

  const [page, setIndex] = useState(0);
  const [pageSize] = usePageSize();

  const start = page * pageSize;

  const results = useQuery(
    [...queryKey, QueryKeys.Range, { start, size: pageSize }],
    () => {
      const param: Parameter.Range = {
        start,
        length: pageSize,
      };
      return queryFn(param);
    },
    {
      onSuccess: ({ data }) => {
        data.forEach((item) => {
          const id = GetItemId(item);
          if (id) {
            client.setQueryData([...queryKey, id], item);
          }
        });
      },
    }
  );

  const { data } = results;

  const totalCount = data?.total ?? 0;
  const pageCount = Math.ceil(totalCount / pageSize);

  const previousPage = useCallback(() => {
    setIndex((index) => Math.max(0, index - 1));
  }, []);

  const nextPage = useCallback(() => {
    if (pageCount > 0) {
      setIndex((index) => Math.min(pageCount - 1, index + 1));
    }
  }, [pageCount]);

  const gotoPage = useCallback(
    (idx: number) => {
      if (idx >= 0 && idx < pageCount) {
        setIndex(idx);
      }
    },
    [pageCount]
  );

  // Reset page index if we out of bound
  useEffect(() => {
    if (pageCount === 0) return;

    if (page >= pageCount) {
      setIndex(pageCount - 1);
    } else if (page < 0) {
      setIndex(0);
    }
  }, [page, pageCount]);

  return {
    ...results,
    paginationStatus: {
      totalCount,
      pageCount,
      pageSize,
      page,
      canPrevious: page > 0,
      canNext: page < pageCount - 1,
    },
    controls: {
      gotoPage,
      previousPage,
      nextPage,
    },
  };
}
