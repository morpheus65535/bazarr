import { FunctionComponent, useMemo } from "react";
import { Checkbox } from "@mantine/core";
import { useDocumentTitle } from "@mantine/hooks";
import { useMovieModification, useMovies } from "@/apis/hooks";
import { useInstanceName } from "@/apis/hooks/site";
import { QueryOverlay } from "@/components/async";
import { AudioList } from "@/components/bazarr";
import LanguageProfileName from "@/components/bazarr/LanguageProfile";
import { AppColumnDef as ColumnDef } from "@/components/tables/features";
import MassEditor from "@/pages/views/MassEditor";
import { useListQueryState } from "@/utilities";

const MovieMassEditor: FunctionComponent = () => {
  // Carry over the filters from the list page (preserved in the URL by the
  // Mass Edit button) so the editor shows the same subset.
  const { query: listState } = useListQueryState("movies");
  const query = useMovies(listState);
  const mutation = useMovieModification();

  useDocumentTitle(`Movies - ${useInstanceName()} (Mass Editor)`);

  const columns = useMemo<ColumnDef<Item.Movie>[]>(
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
            original: { audioLanguage },
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

export default MovieMassEditor;
