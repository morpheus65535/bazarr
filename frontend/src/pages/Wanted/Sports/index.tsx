import { FunctionComponent, useMemo } from "react";
import { Badge, Group } from "@mantine/core";
import { useSportsLeagueAction, useSportsWantedPagination } from "@/apis/hooks";
import Language from "@/components/bazarr/Language";
import { AppColumnDef as ColumnDef } from "@/components/tables/features";
import WantedView from "@/pages/views/WantedView";
import { BuildKey } from "@/utilities";

const WantedSportsView: FunctionComponent = () => {
  const columns = useMemo<ColumnDef<Wanted.SportsEvent>[]>(
    () => [
      {
        header: "League",
        accessorKey: "leagueTitle",
      },
      {
        header: "Event",
        accessorKey: "eventTitle",
      },
      {
        // The part names which file of the event this row covers. Most events
        // have one file and no part name.
        header: "Part",
        accessorKey: "partName",
      },
      {
        header: "Missing",
        accessorKey: "missingSubtitles",
        cell: ({
          row: {
            original: { missingSubtitles },
          },
        }) => {
          return (
            <Group gap="sm">
              {missingSubtitles.map((item, idx) => (
                <Badge key={BuildKey(idx, item.code2)}>
                  <Language.Text value={item}></Language.Text>
                </Badge>
              ))}
            </Group>
          );
        },
      },
    ],
    [],
  );

  const { mutateAsync } = useSportsLeagueAction();
  const query = useSportsWantedPagination();
  return (
    <WantedView
      name="Sports"
      columns={columns}
      query={query}
      searchAll={() => mutateAsync({ action: "search-wanted" })}
    ></WantedView>
  );
};

export default WantedSportsView;
