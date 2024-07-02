import { MutableRefObject } from "react";
import {
  getCoreRowModel,
  Table,
  TableOptions,
  useReactTable,
} from "@tanstack/react-table";
import NewBaseTable, {
  NewTableStyleProps,
} from "@/components/tables/NewBaseTable";
import { usePageSize } from "@/utilities/storage";

export type NewSimpleTableProps<T extends object> = Omit<
  TableOptions<T>,
  "getCoreRowModel"
> & {
  instanceRef?: MutableRefObject<Table<T> | null>;
  tableStyles?: NewTableStyleProps<T>;
};

export default function NewSimpleTable<T extends object>(
  props: NewSimpleTableProps<T>,
) {
  const { instanceRef, tableStyles, ...options } = props;

  const pageSize = usePageSize();

  const instance = useReactTable({
    ...options,
    getCoreRowModel: getCoreRowModel(),
    autoResetPageIndex: false,
    autoResetExpanded: false,
    pageCount: pageSize,
  });

  if (instanceRef) {
    instanceRef.current = instance;
  }

  return (
    <NewBaseTable tableStyles={tableStyles} instance={instance}></NewBaseTable>
  );
}
