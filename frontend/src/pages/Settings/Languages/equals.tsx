import { useLanguages } from "@/apis/hooks";
import { Action, SimpleTable } from "@/components";
import LanguageSelector from "@/components/bazarr/LanguageSelector";
import { languageEqualsKey } from "@/pages/Settings/keys";
import { useFormActions } from "@/pages/Settings/utilities/FormValues";
import { useSettingValue } from "@/pages/Settings/utilities/hooks";
import { LOG } from "@/utilities/console";
import { faEquals, faTrash } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { Button, Checkbox } from "@mantine/core";
import { FunctionComponent, useCallback, useMemo } from "react";
import { Column } from "react-table";

export interface LanguageEqualImmediateData {
  source: Language.CodeType;
  hi: boolean;
  forced: boolean;
  target: Language.CodeType;
}

export interface LanguageEqualData {
  source: Language.Server;
  hi: boolean;
  forced: boolean;
  target: Language.Server;
}

export function parseEqualData(
  text: string
): LanguageEqualImmediateData | undefined {
  const [first, second] = text.split(":");

  if (first.length === 0 || second.length === 0) {
    return undefined;
  }

  const [source, decoration] = first.split("@");

  if (source.length === 0) {
    return undefined;
  }

  const forced = decoration === "forced";
  const hi = decoration === "hi";

  return {
    source,
    forced,
    hi,
    target: second,
  };
}

export function encodeEqualData(data: LanguageEqualData): string {
  let source = data.source.code3;
  if (data.hi) {
    source += "@hi";
  } else if (data.forced) {
    source += "@forced";
  }

  return `${source}:${data.target.code3}`;
}

export function useLatestLanguageEquals(): LanguageEqualData[] {
  const { data } = useLanguages();

  const latest = useSettingValue<string[]>(languageEqualsKey);

  return useMemo(
    () =>
      latest
        ?.map(parseEqualData)
        .map((parsed) => {
          if (parsed === undefined) {
            return undefined;
          }

          const source = data?.find((value) => value.code3 === parsed.source);
          const target = data?.find((value) => value.code3 === parsed.target);

          if (source === undefined || target === undefined) {
            return undefined;
          }

          return { ...parsed, source, target };
        })
        .filter((v): v is LanguageEqualData => v !== undefined) ?? [],
    [data, latest]
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
    [setValue]
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
        source: enabled,
        hi: false,
        forced: false,
        target: enabled,
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
    [equals, setEquals]
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
    [equals, setEquals]
  );

  const columns = useMemo<Column<LanguageEqualData>[]>(
    () => [
      {
        Header: "Source",
        id: "source-lang",
        accessor: "source",
        Cell: ({ value, row }) => {
          return (
            <LanguageSelector
              enabled
              value={value}
              onChange={(result) => {
                if (result !== null) {
                  update(row.index, { ...row.original, source: result });
                }
              }}
            ></LanguageSelector>
          );
        },
      },
      {
        id: "hi",
        accessor: "hi",
        Cell: ({ value, row }) => {
          return (
            <Checkbox
              label="HI"
              checked={value}
              onChange={({ currentTarget: { checked } }) => {
                update(row.index, {
                  ...row.original,
                  hi: checked,
                  forced: checked ? false : row.original.forced,
                });
              }}
            ></Checkbox>
          );
        },
      },
      {
        id: "Forced",
        accessor: "forced",
        Cell: ({ value, row }) => {
          return (
            <Checkbox
              label="Forced"
              checked={value}
              onChange={({ currentTarget: { checked } }) => {
                update(row.index, {
                  ...row.original,
                  forced: checked,
                  hi: checked ? false : row.original.hi,
                });
              }}
            ></Checkbox>
          );
        },
      },
      {
        id: "equal-icon",
        Cell: () => {
          return <FontAwesomeIcon icon={faEquals} />;
        },
      },
      {
        Header: "Target",
        id: "target-lang",
        accessor: "target",
        Cell: ({ value, row }) => {
          return (
            <LanguageSelector
              enabled
              value={value}
              onChange={(result) => {
                if (result !== null) {
                  update(row.index, { ...row.original, target: result });
                }
              }}
            ></LanguageSelector>
          );
        },
      },
      {
        id: "action",
        accessor: "target",
        Cell: ({ row }) => {
          return (
            <Action
              label="Remove"
              icon={faTrash}
              color="red"
              onClick={() => remove(row.index)}
            ></Action>
          );
        },
      },
    ],
    [remove, update]
  );

  return (
    <>
      <SimpleTable data={equals} columns={columns}></SimpleTable>
      <Button fullWidth disabled={!canAdd} color="light" onClick={add}>
        {canAdd ? "Add Equal" : "No Enabled Languages"}
      </Button>
    </>
  );
};

export default EqualsTable;
