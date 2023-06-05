import { GetItemId, useOnValueChange } from "@/utilities";
import { usePageSize } from "@/utilities/storage";
import { useCallback, useEffect, useState } from "react";
import {
  QueryKey,
  UseQueryResult,
  useQuery,
  useQueryClient,
} from "react-query";
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

export function usePaginationQuery<
  TObject extends object = object,
  TQueryKey extends QueryKey = QueryKey
>(
  queryKey: TQueryKey,
  queryFn: RangeQuery<TObject>,
  cacheIndividual = true
): UsePaginationQueryResult<TObject> {
  const client = useQueryClient();

  const [page, setIndex] = useState(0);
  const pageSize = usePageSize();

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
        if (cacheIndividual) {
          data.forEach((item) => {
            const id = GetItemId(item);
            if (id) {
              client.setQueryData([...queryKey, id], item);
            }
          });
        }
      },
    }
  );

  const { data } = results;

  const totalCount = data?.total ?? 0;
  const pageCount = Math.ceil(totalCount / pageSize);

  const gotoPage = useCallback(
    (idx: number) => {
      if (idx >= 0 && idx < pageCount) {
        setIndex(idx);
      }
    },
    [pageCount]
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
}
