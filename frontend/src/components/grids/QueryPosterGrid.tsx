import { useEffect } from "react";
import { useSearchParams } from "react-router";
import { UsePaginationQueryResult } from "@/apis/queries/hooks";
import PageControl from "@/components/tables/PageControl";
import { LoadingProvider } from "@/contexts";
import { ScrollToTop } from "@/utilities";
import PosterGrid, { PosterGridProps } from "./PosterGrid";

type Props<T extends object> = Omit<PosterGridProps<T>, "data"> & {
  query: UsePaginationQueryResult<T>;
};

export default function QueryPosterGrid<T extends object>(props: Props<T>) {
  const { query, ...remain } = props;

  const {
    data = { data: [], total: 0 },
    paginationStatus: { page, pageCount, totalCount, pageSize, isPageLoading },
    controls: { gotoPage },
  } = query;

  const [searchParams, setSearchParams] = useSearchParams();

  useEffect(() => {
    ScrollToTop();
  }, [page]);

  return (
    <LoadingProvider value={isPageLoading}>
      <PosterGrid {...remain} data={data.data}></PosterGrid>
      <PageControl
        count={pageCount}
        index={page}
        size={pageSize}
        total={totalCount}
        goto={(page) => {
          searchParams.set("page", (page + 1).toString());

          setSearchParams(searchParams, { replace: true });

          gotoPage(page);
        }}
      ></PageControl>
    </LoadingProvider>
  );
}
