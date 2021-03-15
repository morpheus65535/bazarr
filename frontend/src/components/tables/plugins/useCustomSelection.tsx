import React, { forwardRef, useEffect, useRef } from "react";
import { Form } from "react-bootstrap";
import {
  CellProps,
  Column,
  ColumnInstance,
  ensurePluginOrder,
  HeaderProps,
  Hooks,
  MetaBase,
  TableInstance,
  TableToggleCommonProps,
} from "react-table";

const pluginName = "useSelection";

const checkboxId = "---selection---";

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

function useSelection<T extends object>(hooks: Hooks<T>) {
  hooks.visibleColumnsDeps.push((deps, { instance }) => [
    ...deps,
    instance.select,
  ]);
  hooks.visibleColumns.push(visibleColumns);
  hooks.useInstance.push(useInstance);
}

useSelection.pluginName = pluginName;

function useInstance<T extends object>(instance: TableInstance<T>) {
  const {
    plugins,
    rows,
    onSelect,
    select,
    state: { selectedRowIds },
  } = instance;

  ensurePluginOrder(plugins, ["useRowSelect"], pluginName);

  useEffect(() => {
    // Performance
    if (select) {
      const items = Object.keys(selectedRowIds).flatMap(
        (v) => rows.find((n) => n.id === v)?.original ?? []
      );
      onSelect && onSelect(items);
    }
  }, [selectedRowIds, onSelect, rows, select]);
}

function visibleColumns<T extends object>(
  columns: ColumnInstance<T>[],
  meta: MetaBase<T>
): Column<T>[] {
  const { instance } = meta;
  if (instance.select) {
    const checkbox: Column<T> = {
      id: checkboxId,
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
    };
    return [checkbox, ...columns.filter((v) => v.selectHide !== true)];
  } else {
    return columns;
  }
}

export default useSelection;
