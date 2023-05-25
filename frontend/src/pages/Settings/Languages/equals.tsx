import { useLanguages } from "@/apis/hooks";
import { SimpleTable } from "@/components";
import LanguageSelector from "@/components/bazarr/LanguageSelector";
import { languageEqualsKey } from "@/pages/Settings/keys";
import { useSettingValue } from "@/pages/Settings/utilities/hooks";
import { faEquals } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { Button, Checkbox } from "@mantine/core";
import { FunctionComponent, useMemo } from "react";
import { Column } from "react-table";
import { useLatestEnabledLanguages } from ".";

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

          return { ...parsed, source, target };
        })
        .filter((v): v is LanguageEqualData => v !== undefined) ?? [],
    [data, latest]
  );
}

interface EqualsTableProps {}

const EqualsTable: FunctionComponent<EqualsTableProps> = () => {
  const languages = useLatestEnabledLanguages();
  const canAdd = languages.length !== 0;

  const equals = useLatestLanguageEquals();

  const columns = useMemo<Column<LanguageEqualData>[]>(
    () => [
      {
        Header: "Source",
        id: "source-lang",
        accessor: "source",
        Cell: ({ value }) => {
          return <LanguageSelector enabled value={value}></LanguageSelector>;
        },
      },
      {
        id: "hi",
        accessor: "hi",
        Cell: ({ value }) => {
          return <Checkbox label="HI"></Checkbox>;
        },
      },
      {
        id: "Forced",
        accessor: "forced",
        Cell: ({ value }) => {
          return <Checkbox label="Forced"></Checkbox>;
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
        Cell: ({ value }) => {
          return <LanguageSelector enabled value={value}></LanguageSelector>;
        },
      },
    ],
    []
  );

  return (
    <>
      <SimpleTable data={equals} columns={columns}></SimpleTable>
      <Button fullWidth disabled={!canAdd} color="light">
        {canAdd ? "Add Equal" : "No Enabled Languages"}
      </Button>
    </>
  );
};

export default EqualsTable;
