import { forwardRef, useEffect, useRef } from "react";
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
import { Checkbox as MantineCheckbox } from "@mantine/core";

const pluginName = "useCustomSelection";

const checkboxId = "---selection---";

interface CheckboxProps {
  idIn: string;
  disabled?: boolean;
}

const Checkbox = forwardRef<
  HTMLInputElement,
  TableToggleCommonProps & CheckboxProps
>(({ indeterminate, checked, disabled, idIn, ...rest }, ref) => {
  const defaultRef = useRef<HTMLInputElement>(null);
  const resolvedRef = ref || defaultRef;

  useEffect(() => {
    if (typeof resolvedRef === "object" && resolvedRef.current) {
      resolvedRef.current.indeterminate = indeterminate ?? false;

      if (disabled) {
        resolvedRef.current.checked = false;
      } else {
        resolvedRef.current.checked = checked ?? false;
      }
    }
  }, [resolvedRef, indeterminate, checked, disabled]);

  return (
    <MantineCheckbox
      key={idIn}
      disabled={disabled}
      ref={resolvedRef}
      {...rest}
    ></MantineCheckbox>
  );
});

function useCustomSelection<T extends object>(hooks: Hooks<T>) {
  hooks.visibleColumns.push(visibleColumns);
  hooks.useInstance.push(useInstance);
}

useCustomSelection.pluginName = pluginName;

function useInstance<T extends object>(instance: TableInstance<T>) {
  const {
    plugins,
    rows,
    onSelect,
    canSelect,
    state: { selectedRowIds },
  } = instance;

  ensurePluginOrder(plugins, ["useRowSelect"], pluginName);

  useEffect(() => {
    // Performance
    let items = Object.keys(selectedRowIds).flatMap(
      (v) => rows.find((n) => n.id === v)?.original ?? [],
    );

    if (canSelect) {
      items = items.filter((v) => canSelect(v));
    }

    onSelect && onSelect(items);
  }, [selectedRowIds, onSelect, rows, canSelect]);
}

function visibleColumns<T extends object>(
  columns: ColumnInstance<T>[],
  meta: MetaBase<T>,
): Column<T>[] {
  const { instance } = meta;
  const checkbox: Column<T> = {
    id: checkboxId,
    Header: ({ getToggleAllRowsSelectedProps }: HeaderProps<T>) => (
      <Checkbox
        idIn="table-header-selection"
        {...getToggleAllRowsSelectedProps()}
      ></Checkbox>
    ),
    Cell: ({ row }: CellProps<T>) => {
      const canSelect = instance.canSelect;
      const disabled = (canSelect && !canSelect(row.original)) ?? false;
      return (
        <Checkbox
          idIn={`table-cell-${row.index}`}
          disabled={disabled}
          {...row.getToggleRowSelectedProps()}
        ></Checkbox>
      );
    },
  };
  return [checkbox, ...columns];
}

export default useCustomSelection;
