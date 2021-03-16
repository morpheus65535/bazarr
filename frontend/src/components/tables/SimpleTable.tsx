import { TableOptions, useTable } from "react-table";
import BaseTable, { TableStyleProps, useStyleAndOptions } from "./BaseTable";
import { useDefaultSettings } from "./plugins";

type Props<T extends object> = TableOptions<T> & TableStyleProps;

export default function SimpleTable<T extends object>(props: Props<T>) {
  const { style, options } = useStyleAndOptions(props);

  const instance = useTable(options, useDefaultSettings);

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
