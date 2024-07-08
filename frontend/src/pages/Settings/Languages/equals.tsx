import { FunctionComponent, useCallback, useMemo } from "react";
import { Button, Checkbox } from "@mantine/core";
import { faEquals, faTrash } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { ColumnDef } from "@tanstack/react-table";
import { useLanguages } from "@/apis/hooks";
import { Action } from "@/components";
import LanguageSelector from "@/components/bazarr/LanguageSelector";
import SimpleTable from "@/components/tables/SimpleTable";
import { languageEqualsKey } from "@/pages/Settings/keys";
import { useFormActions } from "@/pages/Settings/utilities/FormValues";
import { useSettingValue } from "@/pages/Settings/utilities/hooks";
import { LOG } from "@/utilities/console";

interface GenericEqualTarget<T> {
  content: T;
  hi: boolean;
  forced: boolean;
}

interface LanguageEqualGenericData<T> {
  source: GenericEqualTarget<T>;
  target: GenericEqualTarget<T>;
}

export type LanguageEqualImmediateData =
  LanguageEqualGenericData<Language.CodeType>;

export type LanguageEqualData = LanguageEqualGenericData<Language.Server>;

function decodeEqualTarget(
  text: string,
): GenericEqualTarget<Language.CodeType> | undefined {
  const [code, decoration] = text.split("@");

  if (code.length === 0) {
    return undefined;
  }

  const forced = decoration === "forced";
  const hi = decoration === "hi";

  return {
    content: code,
    forced,
    hi,
  };
}

export function decodeEqualData(
  text: string,
): LanguageEqualImmediateData | undefined {
  const [first, second] = text.split(":");

  const source = decodeEqualTarget(first);
  const target = decodeEqualTarget(second);

  if (source === undefined || target === undefined) {
    return undefined;
  }

  return {
    source,
    target,
  };
}

function encodeEqualTarget(data: GenericEqualTarget<Language.Server>): string {
  let text = data.content.code3;
  if (data.hi) {
    text += "@hi";
  } else if (data.forced) {
    text += "@forced";
  }

  return text;
}

export function encodeEqualData(data: LanguageEqualData): string {
  const source = encodeEqualTarget(data.source);
  const target = encodeEqualTarget(data.target);

  return `${source}:${target}`;
}

export function useLatestLanguageEquals(): LanguageEqualData[] {
  const { data } = useLanguages();

  const latest = useSettingValue<string[]>(languageEqualsKey);

  return useMemo(
    () =>
      latest
        ?.map(decodeEqualData)
        .map((parsed) => {
          if (parsed === undefined) {
            return undefined;
          }

          const source = data?.find(
            (value) => value.code3 === parsed.source.content,
          );
          const target = data?.find(
            (value) => value.code3 === parsed.target.content,
          );

          if (source === undefined || target === undefined) {
            return undefined;
          }

          return {
            source: { ...parsed.source, content: source },
            target: { ...parsed.target, content: target },
          };
        })
        .filter((v): v is LanguageEqualData => v !== undefined) ?? [],
    [data, latest],
  );
}

interface EqualsTableProps {}

const EqualsTable: FunctionComponent<EqualsTableProps> = () => {
  const { data: languages } = useLanguages();
  const canAdd = languages !== undefined;

  const equals = useLatestLanguageEquals();

  const { setValue } = useFormActions();

  const setEquals = useCallback(
    (values: LanguageEqualData[]) => {
      const encodedValues = values.map(encodeEqualData);

      LOG("info", "updating language equals data", values);
      setValue(encodedValues, languageEqualsKey);
    },
    [setValue],
  );

  const add = useCallback(() => {
    if (languages === undefined) {
      return;
    }

    const enabled = languages.find((value) => value.enabled);

    if (enabled === undefined) {
      return;
    }

    const newValue: LanguageEqualData[] = [
      ...equals,
      {
        source: {
          content: enabled,
          hi: false,
          forced: false,
        },
        target: {
          content: enabled,
          hi: false,
          forced: false,
        },
      },
    ];

    setEquals(newValue);
  }, [equals, languages, setEquals]);

  const update = useCallback(
    (index: number, value: LanguageEqualData) => {
      if (index < 0 || index >= equals.length) {
        return;
      }

      const newValue: LanguageEqualData[] = [...equals];

      newValue[index] = { ...value };
      setEquals(newValue);
    },
    [equals, setEquals],
  );

  const remove = useCallback(
    (index: number) => {
      if (index < 0 || index >= equals.length) {
        return;
      }

      const newValue: LanguageEqualData[] = [...equals];

      newValue.splice(index, 1);

      setEquals(newValue);
    },
    [equals, setEquals],
  );

  const columns = useMemo<ColumnDef<LanguageEqualData>[]>(
    () => [
      {
        header: "Source",
        id: "source-lang",
        accessorKey: "source",
        cell: ({ row: { original, index } }) => {
          return (
            <LanguageSelector
              enabled
              value={original.source.content}
              onChange={(result) => {
                if (result !== null) {
                  update(index, {
                    ...original,
                    source: { ...original.source, content: result },
                  });
                }
              }}
            ></LanguageSelector>
          );
        },
      },
      {
        id: "source-hi",
        cell: ({ row }) => {
          return (
            <Checkbox
              label="HI"
              checked={row.original.source.hi}
              onChange={({ currentTarget: { checked } }) => {
                update(row.index, {
                  ...row.original,
                  source: {
                    ...row.original.source,
                    hi: checked,
                    forced: checked ? false : row.original.source.forced,
                  },
                });
              }}
            ></Checkbox>
          );
        },
      },
      {
        id: "source-forced",
        cell: ({ row }) => {
          return (
            <Checkbox
              label="Forced"
              checked={row.original.source.forced}
              onChange={({ currentTarget: { checked } }) => {
                update(row.index, {
                  ...row.original,
                  source: {
                    ...row.original.source,
                    forced: checked,
                    hi: checked ? false : row.original.source.hi,
                  },
                });
              }}
            ></Checkbox>
          );
        },
      },
      {
        id: "equal-icon",
        cell: () => {
          return <FontAwesomeIcon icon={faEquals} />;
        },
      },
      {
        header: "Target",
        id: "target-lang",
        cell: ({ row }) => {
          return (
            <LanguageSelector
              enabled
              value={row.original.target.content}
              onChange={(result) => {
                if (result !== null) {
                  update(row.index, {
                    ...row.original,
                    target: { ...row.original.target, content: result },
                  });
                }
              }}
            ></LanguageSelector>
          );
        },
      },
      {
        id: "target-hi",
        cell: ({ row }) => {
          return (
            <Checkbox
              label="HI"
              checked={row.original.target.hi}
              onChange={({ currentTarget: { checked } }) => {
                update(row.index, {
                  ...row.original,
                  target: {
                    ...row.original.target,
                    hi: checked,
                    forced: checked ? false : row.original.target.forced,
                  },
                });
              }}
            ></Checkbox>
          );
        },
      },
      {
        id: "target-forced",
        cell: ({ row }) => {
          return (
            <Checkbox
              label="Forced"
              checked={row.original.target.forced}
              onChange={({ currentTarget: { checked } }) => {
                update(row.index, {
                  ...row.original,
                  target: {
                    ...row.original.target,
                    forced: checked,
                    hi: checked ? false : row.original.target.hi,
                  },
                });
              }}
            ></Checkbox>
          );
        },
      },
      {
        id: "action",
        cell: ({ row }) => {
          return (
            <Action
              label="Remove"
              icon={faTrash}
              c="red"
              onClick={() => remove(row.index)}
            ></Action>
          );
        },
      },
    ],
    [remove, update],
  );

  return (
    <>
      <SimpleTable data={equals} columns={columns}></SimpleTable>
      <Button fullWidth disabled={!canAdd} onClick={add}>
        {canAdd ? "Add Equal" : "No Enabled Languages"}
      </Button>
    </>
  );
};

export default EqualsTable;
