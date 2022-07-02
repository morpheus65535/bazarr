import { ScrollToTop } from "@/utilities";
import { useEffect } from "react";
import { usePagination, useTable } from "react-table";
import BaseTable from "./BaseTable";
import PageControl from "./PageControl";
import { useDefaultSettings } from "./plugins";
import { SimpleTableProps } from "./SimpleTable";

type Props<T extends object> = SimpleTableProps<T> & {
  autoScroll?: boolean;
};

const tablePlugins = [useDefaultSettings, usePagination];

export default function PageTable<T extends object>(props: Props<T>) {
  const { autoScroll = true, plugins, instanceRef, ...options } = props;

  const instance = useTable(
    options,
    useDefaultSettings,
    ...tablePlugins,
    ...(plugins ?? [])
  );

  if (instanceRef) {
    instanceRef.current = instance;
  }

  // Scroll to top when page is changed
  useEffect(() => {
    if (autoScroll) {
      ScrollToTop();
    }
  }, [instance.state.pageIndex, autoScroll]);

  return (
    <>
      <BaseTable
        {...options}
        {...instance}
        plugins={[...tablePlugins, ...(plugins ?? [])]}
      ></BaseTable>
      <PageControl
        count={instance.pageCount}
        index={instance.state.pageIndex}
        size={instance.state.pageSize}
        total={instance.rows.length}
        goto={instance.gotoPage}
      ></PageControl>
    </>
  );
}
