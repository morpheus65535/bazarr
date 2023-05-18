import { SimpleTable } from "@/components";
import { faEquals } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { Button, Checkbox } from "@mantine/core";
import { FunctionComponent, useMemo } from "react";
import { Column } from "react-table";
import { useLatestEnabledLanguages } from ".";

interface LanguageEqualData {
  source: Language.Server;
  hi: boolean;
  forced: boolean;
  target: Language.Server;
}

interface EqualsTableProps {}

const EqualsTable: FunctionComponent<EqualsTableProps> = () => {
  const languages = useLatestEnabledLanguages();
  const canAdd = languages.length !== 0;

  const columns = useMemo<Column<LanguageEqualData>[]>(
    () => [
      {
        Header: "Source",
        id: "source-lang",
        accessor: "source",
        Cell: ({ value }) => {
          return value.name;
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
          return value.name;
        },
      },
    ],
    []
  );

  return (
    <>
      <SimpleTable
        data={[
          {
            source: {
              name: "Chinese",
              code2: "zh",
              code3: "zhs",
              enabled: true,
            },
            hi: false,
            forced: false,
            target: {
              name: "Chinese",
              code2: "zh",
              code3: "zht",
              enabled: true,
            },
          },
        ]}
        columns={columns}
      ></SimpleTable>
      <Button fullWidth disabled={!canAdd} color="light">
        {canAdd ? "Add Equal" : "No Enabled Languages"}
      </Button>
    </>
  );
};

export default EqualsTable;
