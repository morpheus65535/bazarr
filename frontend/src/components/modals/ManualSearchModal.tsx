import { withModal } from "@/modules/modals";
import { task, TaskGroup } from "@/modules/task";
import { useTableStyles } from "@/styles";
import { BuildKey, GetItemId } from "@/utilities";
import {
  faCaretDown,
  faCheck,
  faCheckCircle,
  faDownload,
  faExclamationCircle,
  faInfoCircle,
  faTimes,
} from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import {
  Alert,
  Anchor,
  Badge,
  Button,
  Code,
  Collapse,
  Divider,
  Group,
  List,
  Popover,
  Stack,
  Text,
} from "@mantine/core";
import { useHover } from "@mantine/hooks";
import { isString } from "lodash";
import { FunctionComponent, useCallback, useMemo, useState } from "react";
import { UseQueryResult } from "react-query";
import { Column } from "react-table";
import { Action, PageTable } from "..";
import Language from "../bazarr/Language";

type SupportType = Item.Movie | Item.Episode;

interface Props<T extends SupportType> {
  download: (item: T, result: SearchResultType) => Promise<void>;
  query: (
    id?: number
  ) => UseQueryResult<SearchResultType[] | undefined, unknown>;
  item: T;
}

function ManualSearchView<T extends SupportType>(props: Props<T>) {
  const { download, query: useSearch, item } = props;

  const itemId = useMemo(() => GetItemId(item ?? {}), [item]);

  const [id, setId] = useState<number | undefined>(undefined);

  const results = useSearch(id);

  const isStale = results.data === undefined;

  const search = useCallback(() => {
    setId(itemId);
    results.refetch();
  }, [itemId, results]);

  const columns = useMemo<Column<SearchResultType>[]>(
    () => [
      {
        Header: "Score",
        accessor: "score",
        Cell: ({ value }) => {
          const { classes } = useTableStyles();
          return <Text className={classes.noWrap}>{value}%</Text>;
        },
      },
      {
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
          const { classes } = useTableStyles();
          const value = row.value;
          const { url } = row.row.original;
          if (url) {
            return (
              <Anchor
                className={classes.noWrap}
                href={url}
                target="_blank"
                rel="noopener noreferrer"
              >
                {value}
              </Anchor>
            );
          } else {
            return value;
          }
        },
      },
      {
        Header: "Release",
        accessor: "release_info",
        Cell: ({ value }) => {
          const { classes } = useTableStyles();
          const [open, setOpen] = useState(false);

          const items = useMemo(
            () => value.slice(1).map((v, idx) => <Text key={idx}>{v}</Text>),
            [value]
          );

          if (value.length === 0) {
            return <Text color="dimmed">Cannot get release info</Text>;
          }

          return (
            <Stack spacing={0} onClick={() => setOpen((o) => !o)}>
              <Text className={classes.primary}>
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
        Header: "Upload",
        accessor: "uploader",
        Cell: ({ value }) => {
          const { classes } = useTableStyles();
          return <Text className={classes.noWrap}>{value ?? "-"}</Text>;
        },
      },
      {
        accessor: "matches",
        Cell: (row) => {
          const { matches, dont_matches } = row.row.original;
          return <StateIcon matches={matches} dont={dont_matches}></StateIcon>;
        },
      },
      {
        accessor: "subtitle",
        Cell: ({ row }) => {
          const result = row.original;
          return (
            <Action
              label="Download"
              icon={faDownload}
              color="brand"
              variant="light"
              disabled={item === null}
              onClick={() => {
                if (!item) return;

                task.create(
                  item.title,
                  TaskGroup.DownloadSubtitle,
                  download,
                  item,
                  result
                );
              }}
            ></Action>
          );
        },
      },
    ],
    [download, item]
  );

  const bSceneNameAvailable =
    isString(item.sceneName) && item.sceneName.length !== 0;

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
      <Collapse in={!isStale && !results.isFetching}>
        <PageTable
          tableStyles={{ emptyText: "No result", placeholder: 10 }}
          columns={columns}
          data={results.data ?? []}
        ></PageTable>
      </Collapse>
      <Divider></Divider>
      <Button loading={results.isFetching} fullWidth onClick={search}>
        {isStale ? "Search" : "Search Again"}
      </Button>
    </Stack>
  );
}

export const MovieSearchModal = withModal<Props<Item.Movie>>(
  ManualSearchView,
  "movie-manual-search",
  { title: "Search Subtitles", size: "xl" }
);
export const EpisodeSearchModal = withModal<Props<Item.Episode>>(
  ManualSearchView,
  "episode-manual-search",
  { title: "Search Subtitles", size: "xl" }
);

const StateIcon: FunctionComponent<{ matches: string[]; dont: string[] }> = ({
  matches,
  dont,
}) => {
  const hasIssues = dont.length > 0;

  const { ref, hovered } = useHover();

  return (
    <Popover opened={hovered} position="top">
      <Popover.Target>
        <Text color={hasIssues ? "yellow" : "green"} ref={ref}>
          <FontAwesomeIcon
            icon={hasIssues ? faExclamationCircle : faCheckCircle}
          ></FontAwesomeIcon>
        </Text>
      </Popover.Target>
      <Group align="flex-start" spacing="xl">
        <Stack align="flex-start" spacing="xs">
          <Text color="green">
            <FontAwesomeIcon icon={faCheck}></FontAwesomeIcon>
          </Text>
          <List>
            {matches.map((v, idx) => (
              <List.Item key={BuildKey(idx, v, "match")}>{v}</List.Item>
            ))}
          </List>
        </Stack>
        <Stack align="flex-start" spacing="xs">
          <Text color="yellow">
            <FontAwesomeIcon icon={faTimes}></FontAwesomeIcon>
          </Text>
          <List>
            {dont.map((v, idx) => (
              <List.Item key={BuildKey(idx, v, "miss")}>{v}</List.Item>
            ))}
          </List>
        </Stack>
      </Group>
    </Popover>
  );
};
