import { useEpisodeDeleteBlacklist } from "@/apis/hooks";
import { PageTable } from "@/components";
import { AsyncButton } from "@/components/async";
import Language from "@/components/bazarr/Language";
import TextPopover from "@/components/TextPopover";
import { faTrash } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { Anchor, Text } from "@mantine/core";
import { FunctionComponent, useMemo } from "react";
import { Link } from "react-router-dom";
import { Column } from "react-table";

interface Props {
  blacklist: readonly Blacklist.Episode[];
}

const Table: FunctionComponent<Props> = ({ blacklist }) => {
  const columns = useMemo<Column<Blacklist.Episode>[]>(
    () => [
      {
        Header: "Series",
        accessor: "seriesTitle",
        className: "text-nowrap",
        Cell: (row) => {
          const target = `/series/${row.row.original.sonarrSeriesId}`;
          return (
            <Anchor component={Link} to={target}>
              <Text>{row.value}</Text>
            </Anchor>
          );
        },
      },
      {
        Header: "Episode",
        accessor: "episode_number",
      },
      {
        accessor: "episodeTitle",
      },
      {
        Header: "Language",
        accessor: "language",
        Cell: ({ value }) => {
          if (value) {
            return <Language.Text value={value} long></Language.Text>;
          } else {
            return null;
          }
        },
      },
      {
        Header: "Provider",
        accessor: "provider",
      },
      {
        Header: "Date",
        accessor: "timestamp",
        Cell: (row) => {
          if (row.value) {
            return (
              <TextPopover text={row.row.original.parsed_timestamp}>
                <Text>{row.value}</Text>
              </TextPopover>
            );
          } else {
            return null;
          }
        },
      },
      {
        accessor: "subs_id",
        Cell: ({ row, value }) => {
          const { mutateAsync } = useEpisodeDeleteBlacklist();

          return (
            <AsyncButton
              noReset
              promise={() =>
                mutateAsync({
                  all: false,
                  form: {
                    provider: row.original.provider,
                    subs_id: value,
                  },
                })
              }
            >
              <FontAwesomeIcon icon={faTrash}></FontAwesomeIcon>
            </AsyncButton>
          );
        },
      },
    ],
    []
  );
  return (
    <PageTable
      emptyText="No Blacklisted Series Subtitles"
      columns={columns}
      data={blacklist}
    ></PageTable>
  );
};

export default Table;
