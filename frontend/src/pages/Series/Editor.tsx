import { useSeries, useSeriesModification } from "@/apis/hooks";
import { QueryOverlay } from "@/components/async";
import { Language } from "@/components/bazarr";
import LanguageProfileName from "@/components/bazarr/LanguageProfile";
import MassEditor from "@/components/MassEditor";
import { FunctionComponent, useMemo } from "react";
import { Helmet } from "react-helmet";
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

  return (
    <QueryOverlay result={query}>
      <>
        <Helmet>
          <title>Series - Bazarr (Mass Editor)</title>
        </Helmet>
        <MassEditor
          columns={columns}
          data={query.data ?? []}
          mutation={mutation}
        ></MassEditor>
      </>
    </QueryOverlay>
  );
};

export default SeriesMassEditor;
