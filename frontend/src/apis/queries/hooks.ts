import { GetItemId } from "@/utilities";
import { usePageSize } from "@/utilities/storage";
import { useCallback, useEffect, useState } from "react";
import {
  QueryKey,
  useQuery,
  useQueryClient,
  UseQueryResult,
} from "react-query";
import { QueryKeys } from "./keys";

export type UsePaginationQueryResult<T extends object> = UseQueryResult<
  DataWrapperWithTotal<T>
> & {
  controls: {
    gotoPage: (index: number) => void;
  };
  paginationStatus: {
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
  queryFn: RangeQuery<TObject>
): UsePaginationQueryResult<TObject> {
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
    },
    controls: {
      gotoPage,
    },
  };
}
