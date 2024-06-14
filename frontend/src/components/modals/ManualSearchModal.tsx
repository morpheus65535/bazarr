import { useCallback, useMemo, useState } from "react";
import { Column } from "react-table";
import {
  Alert,
  Anchor,
  Badge,
  Button,
  Code,
  Collapse,
  Divider,
  Stack,
  Text,
} from "@mantine/core";
import {
  faCaretDown,
  faDownload,
  faInfoCircle,
} from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { UseQueryResult } from "@tanstack/react-query";
import { isString } from "lodash";
import { Action, PageTable } from "@/components";
import Language from "@/components/bazarr/Language";
import StateIcon from "@/components/StateIcon";
import { withModal } from "@/modules/modals";
import { task, TaskGroup } from "@/modules/task";
import { GetItemId } from "@/utilities";

type SupportType = Item.Movie | Item.Episode;

interface Props<T extends SupportType> {
  download: (item: T, result: SearchResultType) => Promise<void>;
  query: (id?: number) => UseQueryResult<SearchResultType[] | undefined>;
  item: T;
}

function ManualSearchView<T extends SupportType>(props: Props<T>) {
  const { download, query: useSearch, item } = props;

  const [searchStarted, setSearchStarted] = useState(false);

  const itemId = useMemo(() => GetItemId(item), [item]);

  const results = useSearch(searchStarted ? itemId : undefined);

  const haveResult = results.data !== undefined;

  const search = useCallback(() => {
    setSearchStarted(true);

    void results.refetch();
  }, [results]);

  const columns = useMemo<Column<SearchResultType>[]>(
    () => [
      {
        Header: "Score",
        accessor: "score",
        Cell: ({ value }) => {
          return <Text className="table-no-wrap">{value}%</Text>;
        },
      },
      {
        Header: "Language",
        accessor: "language",
        Cell: ({ row: { original }, value }) => {
          const lang: Language.Info = {
            code2: value,
            hi: original.hearing_impaired === "True",
            forced: original.forced === "True",
            name: "",
          };
          return (
            <Badge>
              <Language.Text value={lang}></Language.Text>
            </Badge>
          );
        },
      },
      {
        Header: "Provider",
        accessor: "provider",
        Cell: (row) => {
          const value = row.value;
          const { url } = row.row.original;
          if (url) {
            return (
              <Anchor
                className="table-no-wrap"
                href={url}
                target="_blank"
                rel="noopener noreferrer"
              >
                {value}
              </Anchor>
            );
          } else {
            return <Text>{value}</Text>;
          }
        },
      },
      {
        Header: "Release",
        accessor: "release_info",
        Cell: ({ value }) => {
          const [open, setOpen] = useState(false);

          const items = useMemo(
            () => value.slice(1).map((v, idx) => <Text key={idx}>{v}</Text>),
            [value],
          );

          if (value.length === 0) {
            return <Text c="dimmed">Cannot get release info</Text>;
          }

          return (
            <Stack gap={0} onClick={() => setOpen((o) => !o)}>
              <Text className="table-primary" span>
                {value[0]}
                {value.length > 1 && (
                  <FontAwesomeIcon
                    icon={faCaretDown}
                    rotation={open ? 180 : undefined}
                  ></FontAwesomeIcon>
                )}
              </Text>
              <Collapse in={open}>
                <>{items}</>
              </Collapse>
            </Stack>
          );
        },
      },
      {
        Header: "Uploader",
        accessor: "uploader",
        Cell: ({ value }) => {
          return <Text className="table-no-wrap">{value ?? "-"}</Text>;
        },
      },
      {
        Header: "Match",
        accessor: "matches",
        Cell: (row) => {
          const { matches, dont_matches: dont } = row.row.original;
          return (
            <StateIcon
              matches={matches}
              dont={dont}
              isHistory={false}
            ></StateIcon>
          );
        },
      },
      {
        Header: "Get",
        accessor: "subtitle",
        Cell: ({ row }) => {
          const result = row.original;
          return (
            <Action
              label="Download"
              icon={faDownload}
              c="brand"
              disabled={item === null}
              onClick={() => {
                if (!item) return;

                task.create(
                  item.title,
                  TaskGroup.DownloadSubtitle,
                  download,
                  item,
                  result,
                );
              }}
            ></Action>
          );
        },
      },
    ],
    [download, item],
  );

  const bSceneNameAvailable =
    isString(item.sceneName) && item.sceneName.length !== 0;

  const searchButtonText = useMemo(() => {
    if (results.isFetching) {
      return "Searching";
    }

    return searchStarted ? "Search Again" : "Search";
  }, [results.isFetching, searchStarted]);

  return (
    <Stack>
      <Alert
        title="Resource"
        color="gray"
        icon={<FontAwesomeIcon icon={faInfoCircle}></FontAwesomeIcon>}
      >
        <Text size="sm">{item?.path}</Text>
        <Divider hidden={!bSceneNameAvailable} my="xs"></Divider>
        <Code hidden={!bSceneNameAvailable}>{item?.sceneName}</Code>
      </Alert>
      <Collapse in={haveResult && !results.isFetching}>
        <PageTable
          autoScroll={false}
          tableStyles={{ emptyText: "No result", placeholder: 10 }}
          columns={columns}
          data={results.data ?? []}
        ></PageTable>
      </Collapse>
      <Divider></Divider>
      <Button loading={results.isFetching} fullWidth onClick={search}>
        {searchButtonText}
      </Button>
    </Stack>
  );
}

export const MovieSearchModal = withModal<Props<Item.Movie>>(
  ManualSearchView,
  "movie-manual-search",
  { title: "Search Subtitles", size: "calc(100vw - 4rem)" },
);
export const EpisodeSearchModal = withModal<Props<Item.Episode>>(
  ManualSearchView,
  "episode-manual-search",
  { title: "Search Subtitles", size: "calc(100vw - 4rem)" },
);
