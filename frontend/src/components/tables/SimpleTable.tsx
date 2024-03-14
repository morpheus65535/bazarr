import { PluginHook, TableInstance, TableOptions, useTable } from "react-table";
import BaseTable, { TableStyleProps } from "./BaseTable";
import { useDefaultSettings } from "./plugins";

export type SimpleTableProps<T extends object> = TableOptions<T> & {
  plugins?: PluginHook<T>[];
  instanceRef?: React.MutableRefObject<TableInstance<T> | null>;
  tableStyles?: TableStyleProps<T>;
};

export default function SimpleTable<T extends object>(
  props: SimpleTableProps<T>,
) {
  const { plugins, instanceRef, tableStyles, ...options } = props;

  const instance = useTable(options, useDefaultSettings, ...(plugins ?? []));

  if (instanceRef) {
    instanceRef.current = instance;
  }

  return <BaseTable tableStyles={tableStyles} {...instance}></BaseTable>;
}
