import { TableOptions, useTable } from "react-table";
import BaseTable, {
  ExtractStyleAndOptions,
  TableStyleProps,
} from "./BaseTable";

type Props<T extends object> = TableOptions<T> & TableStyleProps;

export default function SimpleTable<T extends object>(props: Props<T>) {
  const { style, options } = ExtractStyleAndOptions(props);

  const instance = useTable(options);

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
