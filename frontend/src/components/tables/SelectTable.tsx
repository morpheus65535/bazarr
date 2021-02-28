import React, { forwardRef, useEffect, useRef } from "react";
import { Form } from "react-bootstrap";
import {
  CellProps,
  HeaderProps,
  TableOptions,
  TableToggleCommonProps,
  useRowSelect,
  useTable,
} from "react-table";
import BaseTable, {
  ExtractStyleAndOptions,
  TableStyleProps,
} from "./BaseTable";

interface CheckboxProps {
  idIn: string;
}

const Checkbox = forwardRef<
  HTMLInputElement,
  TableToggleCommonProps & CheckboxProps
>(({ indeterminate, idIn, ...rest }, ref) => {
  const defaultRef = useRef<HTMLInputElement>(null);
  const resolvedRef = ref || defaultRef;

  useEffect(() => {
    if (typeof resolvedRef === "object" && resolvedRef.current) {
      resolvedRef.current.indeterminate = indeterminate ?? false;
    }
  }, [resolvedRef, indeterminate]);

  return <Form.Check custom id={idIn} ref={resolvedRef} {...rest}></Form.Check>;
});

type Props<T extends object> = TableOptions<T> &
  TableStyleProps & {
    onSelect?: (items: T[]) => void;
  };

export default function SelectTable<T extends object>(props: Props<T>) {
  const { onSelect, ...remain } = props;
  const { style, options } = ExtractStyleAndOptions(remain);

  if (options.autoResetSelectedRows === undefined) {
    options.autoResetSelectedRows = false;
  }

  options.isSelecting = true;

  const instance = useTable(options, useRowSelect, (hooks) => {
    hooks.visibleColumns.push((columns) => [
      {
        id: "selection",
        Header: ({ getToggleAllRowsSelectedProps }: HeaderProps<any>) => (
          <Checkbox
            idIn="table-header-selection"
            {...getToggleAllRowsSelectedProps()}
          ></Checkbox>
        ),
        Cell: ({ row }: CellProps<any>) => (
          <Checkbox
            idIn={`table-cell-${row.index}`}
            {...row.getToggleRowSelectedProps()}
          ></Checkbox>
        ),
      },
      ...columns.filter((v) => v.selectHide !== true),
    ]);
  });

  const {
    getTableProps,
    getTableBodyProps,
    headerGroups,
    rows,
    prepareRow,
    state: { selectedRowIds },
  } = instance;

  useEffect(() => {
    // Performance
    const items = Object.keys(selectedRowIds).flatMap(
      (v) => rows.find((n) => n.id === v)?.original ?? []
    );
    onSelect && onSelect(items);
  }, [selectedRowIds, onSelect, rows]);

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
