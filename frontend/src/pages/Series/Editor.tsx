import { useSeries, useSeriesModification } from "@/apis/hooks";
import { QueryOverlay } from "@/components/async";
import { Language } from "@/components/bazarr";
import LanguageProfileName from "@/components/bazarr/LanguageProfile";
import MassEditor from "@/pages/views/MassEditor";
import { useDocumentTitle } from "@mantine/hooks";
import { FunctionComponent, useMemo } from "react";
import { Column } from "react-table";

const SeriesMassEditor: FunctionComponent = () => {
  const query = useSeries();
  const mutation = useSeriesModification();

  const columns = useMemo<Column<Item.Series>[]>(
    () => [
      {
        Header: "Name",
        accessor: "title",
      },
      {
        Header: "Audio",
        accessor: "audio_language",
        Cell: ({ value }) => {
          return <Language.List value={value}></Language.List>;
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
    []
  );

  useDocumentTitle("Series - Bazarr (Mass Editor)");

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
