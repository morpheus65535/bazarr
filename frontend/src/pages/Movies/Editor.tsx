import { FunctionComponent, useMemo } from "react";
import { useDocumentTitle } from "@mantine/hooks";
import { ColumnDef } from "@tanstack/react-table";
import { useMovieModification, useMovies } from "@/apis/hooks";
import { QueryOverlay } from "@/components/async";
import { AudioList } from "@/components/bazarr";
import LanguageProfileName from "@/components/bazarr/LanguageProfile";
import MassEditor from "@/pages/views/MassEditor";

const MovieMassEditor: FunctionComponent = () => {
  const query = useMovies();
  const mutation = useMovieModification();

  const columns = useMemo<ColumnDef<Item.Movie>[]>(
    () => [
      {
        header: "Name",
        accessorKey: "title",
      },
      {
        header: "Audio",
        accessorKey: "audio_language",
        cell: ({
          row: {
            original: { audio_language: audioLanguage },
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

  useDocumentTitle("Movies - Bazarr (Mass Editor)");

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
