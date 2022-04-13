import { ScrollToTop } from "@/utilities";
import { useEffect, useRef } from "react";
import { TableInstance, usePagination } from "react-table";
import PageControl from "./PageControl";
import { useDefaultSettings } from "./plugins";
import SimpleTable, { SimpleTableProps } from "./SimpleTable";

type Props<T extends object> = SimpleTableProps<T> & {
  autoScroll?: boolean;
};

const tablePlugins = [useDefaultSettings, usePagination];

export default function PageTable<T extends object>(props: Props<T>) {
  const { autoScroll, plugins, ...remain } = props;

  const instance = useRef<TableInstance<T> | null>(null);

  // Scroll to top when page is changed
  useEffect(() => {
    if (autoScroll) {
      ScrollToTop();
    }
  }, [instance.current?.state.pageIndex, autoScroll]);

  return (
    <>
      <SimpleTable
        {...remain}
        instanceRef={instance}
        plugins={[...tablePlugins, ...(plugins ?? [])]}
      ></SimpleTable>
      {instance.current && (
        <PageControl
          count={instance.current.pageCount}
          index={instance.current.state.pageIndex}
          size={instance.current.state.pageSize}
          total={instance.current.rows.length}
          goto={instance.current.gotoPage}
        ></PageControl>
      )}
    </>
  );
}
