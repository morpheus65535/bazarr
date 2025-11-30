import React, { useCallback, useMemo, useState } from "react";
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
  faCloudDownloadAlt,
  faDownload,
  faInfoCircle,
} from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { UseQueryResult } from "@tanstack/react-query";
import { ColumnDef } from "@tanstack/react-table";
import { isString } from "lodash";
import { Action } from "@/components";
import Language from "@/components/bazarr/Language";
import StateIcon from "@/components/StateIcon";
import PageTable from "@/components/tables/PageTable";
import { withModal } from "@/modules/modals";
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

  const ReleaseInfoCell = React.memo(
    ({ releaseInfo }: { releaseInfo: string[] }) => {
      const [open, setOpen] = useState(false);

      const items = useMemo(
        () => releaseInfo.slice(1).map((v, idx) => <Text key={idx}>{v}</Text>),
        [releaseInfo],
      );

      if (releaseInfo.length === 0) {
        return <Text c="dimmed">Cannot get release info</Text>;
      }

      return (
        <Stack gap={0} onClick={() => setOpen((o) => !o)}>
          <Text className="table-primary" span>
            {releaseInfo[0]}
            {releaseInfo.length > 1 && (
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
  );

  const [Downloaded, setDownloaded] = useState({ id: "", state: false });

  const columns = useMemo<ColumnDef<SearchResultType>[]>(
    () => [
      {
        header: "Score",
        accessorKey: "score",
        cell: ({
          row: {
            original: { score },
          },
        }) => {
          return <Text className="table-no-wrap">{score}%</Text>;
        },
      },
      {
        header: "Language",
        accessorKey: "language",
        cell: ({
          row: {
            original: { language, hearing_impaired: hi, forced },
          },
        }) => {
          const lang: Language.Info = {
            code2: language,
            hi: hi === "True",
            forced: forced === "True",
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
        header: "Provider",
        accessorKey: "provider",
        cell: ({
          row: {
            original: { provider, url },
          },
        }) => {
          const value = provider;

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
        header: "Release",
        accessorKey: "release_info",
        cell: ({
          row: {
            original: { release_info: releaseInfo },
          },
        }) => {
          return <ReleaseInfoCell releaseInfo={releaseInfo} />;
        },
      },
      {
        header: "Uploader",
        accessorKey: "uploader",
        cell: ({
          row: {
            original: { uploader },
          },
        }) => {
          return <Text className="table-no-wrap">{uploader ?? "-"}</Text>;
        },
      },
      {
        header: "Match",
        accessorKey: "matches",
        cell: (row) => {
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
        header: "Get",
        accessorKey: "subtitle",
        cell: ({ row }) => {
          const result = row.original;
          const isDownloaded = Downloaded.id === row.id && Downloaded.state;
          return (
            <Action
              label="Download"
              icon={isDownloaded ? faCloudDownloadAlt : faDownload}
              color={isDownloaded ? "brand" : "gray"}
              disabled={item === null}
              onClick={async () => {
                if (!item) return;

                setDownloaded({ id: row.id, state: true });
                await download(item, result);
              }}
            ></Action>
          );
        },
      },
    ],
    [download, item, ReleaseInfoCell, Downloaded],
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
