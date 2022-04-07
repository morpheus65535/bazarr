import { withModal } from "@/modules/modals";
import { createAndDispatchTask } from "@/modules/task/utilities";
import { GetItemId } from "@/utilities";
import {
  faCaretDown,
  faDownload,
  faInfoCircle,
} from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import {
  Alert,
  Anchor,
  Badge,
  Button,
  Collapse,
  Divider,
  Stack,
  Text,
} from "@mantine/core";
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
        accessor: (d) => `${d.score}%`,
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
            <Badge color="secondary">
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
              <Anchor href={url} target="_blank" rel="noopener noreferrer">
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
        Cell: (row) => {
          const value = row.value;

          const [open, setOpen] = useState(false);

          const items = useMemo(
            () => value.slice(1).map((v, idx) => <Text key={idx}>{v}</Text>),
            [value]
          );

          if (value.length === 0) {
            return <Text color="dimmed">Cannot get release info</Text>;
          }

          return (
            <div onClick={() => setOpen((o) => !o)}>
              <div>
                <Text>{value[0]}</Text>
                <Collapse in={open}>
                  <div>{items}</div>
                </Collapse>
              </div>

              {value.length > 1 && (
                <FontAwesomeIcon
                  icon={faCaretDown}
                  rotation={open ? 180 : undefined}
                ></FontAwesomeIcon>
              )}
            </div>
          );
        },
      },
      {
        Header: "Upload",
        accessor: (d) => d.uploader ?? "-",
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
              icon={faDownload}
              color="brand"
              variant="light"
              disabled={item === null}
              onClick={() => {
                if (!item) return;

                createAndDispatchTask(
                  item.title,
                  "download-subtitles",
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

  // const title = useMemo(() => {
  //   let title = "Unknown";

  //   if (item) {
  //     if (item.sceneName) {
  //       title = item.sceneName;
  //     } else if (isMovie(item)) {
  //       title = item.title;
  //     } else {
  //       title = item.title;
  //     }
  //   }
  //   return `Search - ${title}`;
  // }, [item]);

  // const Modal = useModal({
  //   size: "xl",
  //   closeable: results.isFetching === false,
  //   onMounted: () => {
  //     // Cleanup the ID when user switches episode / movie
  //     if (itemId !== id) {
  //       setId(undefined);
  //     }
  //   },
  // });

  return (
    <Stack>
      <Alert
        title="Resource"
        color="gray"
        icon={<FontAwesomeIcon icon={faInfoCircle}></FontAwesomeIcon>}
      >
        {item?.path}
      </Alert>
      <Collapse in={!isStale && !results.isFetching}>
        <PageTable
          emptyText="No Result"
          columns={columns}
          placeholder={10}
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
  // let icon = faCheck;
  // let color = "var(--success)";
  // if (dont.length > 0) {
  //   icon = faInfoCircle;
  //   color = "var(--warning)";
  // }

  // const matchElements = useMemo(
  //   () =>
  //     matches.map((v, idx) => (
  //       <p key={`match-${idx}`} className="text-nowrap m-0">
  //         {v}
  //       </p>
  //     )),
  //   [matches]
  // );
  // const dontElements = useMemo(
  //   () =>
  //     dont.map((v, idx) => (
  //       <p key={`dont-${idx}`} className="text-nowrap m-0">
  //         {v}
  //       </p>
  //     )),
  //   [dont]
  // );

  return null;
  // const popover = (
  //   <Popover className="w-100" id="manual-search-matches-info">
  //     <Popover.Content>
  //       <Container fluid>
  //         <Row>
  //           <Col xs={6}>
  //             <FontAwesomeIcon
  //               color="var(--success)"
  //               icon={faCheck}
  //             ></FontAwesomeIcon>
  //             {matchElements}
  //           </Col>
  //           <Col xs={6}>
  //             <FontAwesomeIcon
  //               color="var(--danger)"
  //               icon={faTimes}
  //             ></FontAwesomeIcon>
  //             {dontElements}
  //           </Col>
  //         </Row>
  //       </Container>
  //     </Popover.Content>
  //   </Popover>
  // );

  // return (
  //   <OverlayTrigger overlay={popover} placement={"left"}>
  //     <FontAwesomeIcon icon={icon} color={color}></FontAwesomeIcon>
  //   </OverlayTrigger>
  // );
};
