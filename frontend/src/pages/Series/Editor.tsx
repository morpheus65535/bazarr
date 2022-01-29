import { useSeries, useSeriesModification } from "@/apis/hooks";
import { QueryOverlay } from "@/components";
import LanguageProfile from "@/components/bazarr/LanguageProfile";
import MassEditor from "@/components/MassEditor";
import { BuildKey } from "@/utilities";
import { FunctionComponent, useMemo } from "react";
import { Badge } from "react-bootstrap";
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
        className: "text-nowrap",
      },
      {
        Header: "Audio",
        accessor: "audio_language",
        Cell: (row) => {
          return row.value.map((v) => (
            <Badge
              variant="secondary"
              className="mr-2"
              key={BuildKey(v.code2, v.forced, v.hi)}
            >
              {v.name}
            </Badge>
          ));
        },
      },
      {
        Header: "Languages Profile",
        accessor: "profileId",
        Cell: ({ value }) => {
          return <LanguageProfile index={value}></LanguageProfile>;
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
