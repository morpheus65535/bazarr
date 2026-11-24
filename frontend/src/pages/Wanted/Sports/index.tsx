import { FunctionComponent, useMemo } from "react";
import { Link } from "react-router";
import { Anchor, Badge, Group } from "@mantine/core";
import { faSearch } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import {
  useSportsLeagueAction,
  useSportsSubtitleModification,
  useSportsWantedPagination,
} from "@/apis/hooks";
import Language from "@/components/bazarr/Language";
import { AppColumnDef as ColumnDef } from "@/components/tables/features";
import WantedView from "@/pages/views/WantedView";
import { BuildKey } from "@/utilities";

const WantedSportsView: FunctionComponent = () => {
  const { download } = useSportsSubtitleModification();

  const columns = useMemo<ColumnDef<Wanted.SportsEvent>[]>(
    () => [
      {
        header: "League",
        accessorKey: "leagueTitle",
        cell: ({
          row: {
            original: { sportarrLeagueId, leagueTitle },
          },
        }) => {
          const target = `/sports/${sportarrLeagueId}`;
          return (
            <Anchor className="table-primary" component={Link} to={target}>
              {leagueTitle}
            </Anchor>
          );
        },
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
            original: { sportarrLeagueId, sportsEventId, missingSubtitles },
          },
        }) => {
          return (
            <Group gap="sm">
              {missingSubtitles.map((item, idx) => (
                <Badge
                  color={download.isPending ? "secondary" : undefined}
                  leftSection={<FontAwesomeIcon icon={faSearch} />}
                  key={BuildKey(idx, item.code2)}
                  style={{ cursor: "pointer" }}
                  onClick={async () => {
                    await download.mutateAsync({
                      leagueId: sportarrLeagueId,
                      eventId: sportsEventId,
                      form: {
                        language: item.code2,
                        hi: item.hi,
                        forced: item.forced,
                      },
                    });
                  }}
                >
                  <Language.Text value={item}></Language.Text>
                </Badge>
              ))}
            </Group>
          );
        },
      },
    ],
    [download],
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
