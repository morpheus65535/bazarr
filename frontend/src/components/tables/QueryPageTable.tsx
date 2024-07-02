import { useEffect } from "react";
import { UsePaginationQueryResult } from "@/apis/queries/hooks";
import NewSimpleTable, {
  NewSimpleTableProps,
} from "@/components/tables/NewSimpleTable";
import { LoadingProvider } from "@/contexts";
import { ScrollToTop } from "@/utilities";
import PageControl from "./PageControl";

type Props<T extends object> = Omit<NewSimpleTableProps<T>, "data"> & {
  query: UsePaginationQueryResult<T>;
};

export default function QueryPageTable<T extends object>(props: Props<T>) {
  const { query, ...remain } = props;

  const {
    data = { data: [], total: 0 },
    paginationStatus: { page, pageCount, totalCount, pageSize, isPageLoading },
    controls: { gotoPage },
  } = query;

  useEffect(() => {
    ScrollToTop();
  }, [page]);

  return (
    <LoadingProvider value={isPageLoading}>
      <NewSimpleTable {...remain} data={data.data}></NewSimpleTable>
      <PageControl
        count={pageCount}
        index={page}
        size={pageSize}
        total={totalCount}
        goto={gotoPage}
      ></PageControl>
    </LoadingProvider>
  );
}
