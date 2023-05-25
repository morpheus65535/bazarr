import { SimpleTable } from "@/components";
import LanguageSelector from "@/components/bazarr/LanguageSelector";
import { faEquals } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { Button, Checkbox } from "@mantine/core";
import { FunctionComponent, useMemo } from "react";
import { Column } from "react-table";
import {
  LanguageEqualData,
  useLatestEnabledLanguages,
  useLatestLanguageEquals,
} from ".";

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
