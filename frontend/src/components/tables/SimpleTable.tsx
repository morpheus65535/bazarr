import { PluginHook, TableInstance, TableOptions, useTable } from "react-table";
import BaseTable, { TableStyleProps, useStyleAndOptions } from "./BaseTable";
import { useDefaultSettings } from "./plugins";

export type SimpleTableProps<T extends object> = TableOptions<T> &
  TableStyleProps<T> & {
    plugins?: PluginHook<T>[];
    instanceRef?: React.MutableRefObject<TableInstance<T> | null>;
  };

export default function SimpleTable<T extends object>(
  props: SimpleTableProps<T>
) {
  const { plugins, instanceRef, ...other } = props;
  const { style, options } = useStyleAndOptions(other);

  const instance = useTable(options, useDefaultSettings, ...(plugins ?? []));

  if (instanceRef) {
    instanceRef.current = instance;
  }

  const { getTableProps, getTableBodyProps, headerGroups, rows, prepareRow } =
    instance;

  return (
    <BaseTable
      {...style}
      headers={headerGroups}
      rows={rows}
      prepareRow={prepareRow}
      tableProps={getTableProps()}
      tableBodyProps={getTableBodyProps()}
    ></BaseTable>
  );
}
