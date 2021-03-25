import { PluginHook, TableOptions, useTable } from "react-table";
import BaseTable, { TableStyleProps, useStyleAndOptions } from "./BaseTable";
import { useDefaultSettings } from "./plugins";

type Props<T extends object> = TableOptions<T> &
  TableStyleProps<T> & {
    plugins?: PluginHook<T>[];
  };

export default function SimpleTable<T extends object>(props: Props<T>) {
  const { plugins, ...other } = props;
  const { style, options } = useStyleAndOptions(other);

  const instance = useTable(options, useDefaultSettings, ...(plugins ?? []));

  const {
    getTableProps,
    getTableBodyProps,
    headerGroups,
    rows,
    prepareRow,
  } = instance;

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
