import { useEffect } from "react";
import { useSearchParams } from "react-router";
import { UsePaginationQueryResult } from "@/apis/queries/hooks";
import { RowData } from "@/components/tables/features";
import SimpleTable, { SimpleTableProps } from "@/components/tables/SimpleTable";
import { LoadingProvider } from "@/contexts";
import { ScrollToTop } from "@/utilities";
import PageControl from "./PageControl";

type Props<T extends RowData> = Omit<SimpleTableProps<T>, "data"> & {
  query: UsePaginationQueryResult<T>;
};

export default function QueryPageTable<T extends RowData>(props: Props<T>) {
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
      <SimpleTable {...remain} data={data.data}></SimpleTable>
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
