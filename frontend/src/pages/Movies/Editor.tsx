import { FunctionComponent, useMemo } from "react";
import { Column } from "react-table";
import { useDocumentTitle } from "@mantine/hooks";
import { useMovieModification, useMovies } from "@/apis/hooks";
import { QueryOverlay } from "@/components/async";
import { AudioList } from "@/components/bazarr";
import LanguageProfileName from "@/components/bazarr/LanguageProfile";
import MassEditor from "@/pages/views/MassEditor";

const MovieMassEditor: FunctionComponent = () => {
  const query = useMovies();
  const mutation = useMovieModification();

  const columns = useMemo<Column<Item.Movie>[]>(
    () => [
      {
        Header: "Name",
        accessor: "title",
      },
      {
        Header: "Audio",
        accessor: "audio_language",
        Cell: ({ value }) => {
          return <AudioList audios={value}></AudioList>;
        },
      },
      {
        Header: "Languages Profile",
        accessor: "profileId",
        Cell: ({ value }) => {
          return <LanguageProfileName index={value}></LanguageProfileName>;
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
