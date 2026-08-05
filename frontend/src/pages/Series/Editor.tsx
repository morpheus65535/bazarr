import { FunctionComponent, useMemo } from "react";
import { Checkbox } from "@mantine/core";
import { useDocumentTitle } from "@mantine/hooks";
import { useSeries, useSeriesModification } from "@/apis/hooks";
import { useInstanceName } from "@/apis/hooks/site";
import { QueryOverlay } from "@/components/async";
import { AudioList } from "@/components/bazarr";
import LanguageProfileName from "@/components/bazarr/LanguageProfile";
import { AppColumnDef as ColumnDef } from "@/components/tables/features";
import MassEditor from "@/pages/views/MassEditor";

const SeriesMassEditor: FunctionComponent = () => {
  const query = useSeries();
  const mutation = useSeriesModification();

  const columns = useMemo<ColumnDef<Item.Series>[]>(
    () => [
      {
        id: "selection",
        header: ({ table }) => {
          return (
            <Checkbox
              id="table-header-selection"
              indeterminate={
                table.getIsSomeRowsSelected() && !table.getIsAllRowsSelected()
              }
              checked={table.getIsAllRowsSelected()}
              onChange={table.getToggleAllRowsSelectedHandler()}
            ></Checkbox>
          );
        },
        cell: ({ row }) => {
          return (
            <Checkbox
              id={`table-cell-${row.index}`}
              checked={row.getIsSelected()}
              onChange={row.getToggleSelectedHandler()}
              onClick={row.getToggleSelectedHandler()}
            ></Checkbox>
          );
        },
      },
      {
        header: "Name",
        accessorKey: "title",
      },
      {
        header: "Audio",
        accessorKey: "audioLanguage",
        cell: ({
          row: {
            original: { audioLanguage: audioLanguage },
          },
        }) => {
          return <AudioList audios={audioLanguage}></AudioList>;
        },
      },
      {
        header: "Languages Profile",
        accessorKey: "profileId",
        cell: ({
          row: {
            original: { profileId },
          },
        }) => {
          return <LanguageProfileName index={profileId}></LanguageProfileName>;
        },
      },
    ],
    [],
  );

  useDocumentTitle(`Series - ${useInstanceName()} (Mass Editor)`);

  return (
    <QueryOverlay result={query}>
      <MassEditor
        columns={columns}
        data={query.data ?? []}
        mutation={mutation}
      ></MassEditor>
    </QueryOverlay>
  );
};

export default SeriesMassEditor;
