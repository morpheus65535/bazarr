import { useModal, usePayload, withModal } from "@/modules/modals";
import { createAndDispatchTask } from "@/modules/task/utilities";
import { GetItemId, isMovie } from "@/utilities";
import {
  faCaretDown,
  faCheck,
  faDownload,
  faInfoCircle,
  faTimes,
} from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import {
  Badge,
  Button,
  Col,
  Collapse,
  Container,
  OverlayTrigger,
  Popover,
  Row,
} from "@mantine/core";
import clsx from "clsx";
import { FunctionComponent, useCallback, useMemo, useState } from "react";
import { UseQueryResult } from "react-query";
import { Column } from "react-table";
import { LoadingIndicator, PageTable } from "..";
import Language from "../bazarr/Language";

type SupportType = Item.Movie | Item.Episode;

interface Props<T extends SupportType> {
  download: (item: T, result: SearchResultType) => Promise<void>;
  query: (
    id?: number
  ) => UseQueryResult<SearchResultType[] | undefined, unknown>;
}

function ManualSearchView<T extends SupportType>(props: Props<T>) {
  const { download, query: useSearch } = props;

  const item = usePayload<T>();

  const itemId = useMemo(() => GetItemId(item ?? {}), [item]);

  const [id, setId] = useState<number | undefined>(undefined);

  const results = useSearch(id);

  const isStale = results.data === undefined;

  const search = useCallback(() => {
    if (itemId !== undefined) {
      setId(itemId);
      results.refetch();
    }
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
              <a href={url} target="_blank" rel="noopener noreferrer">
                {value}
              </a>
            );
          } else {
            return value;
          }
        },
      },
      {
        Header: "Release",
        accessor: "release_info",
        className: "text-nowrap",
        Cell: (row) => {
          const value = row.value;

          const [open, setOpen] = useState(false);

          const items = useMemo(
            () =>
              value.slice(1).map((v, idx) => (
                <span className="release-text hidden-item" key={idx}>
                  {v}
                </span>
              )),
            [value]
          );

          if (value.length === 0) {
            return <span className="text-muted">Cannot get release info</span>;
          }

          return (
            <div
              className={clsx(
                "release-container d-flex justify-content-between align-items-center",
                { "release-multi": value.length > 1 }
              )}
              onClick={() => setOpen((o) => !o)}
            >
              <div className="text-container">
                <span className="release-text">{value[0]}</span>
                <Collapse in={open}>
                  <div>{items}</div>
                </Collapse>
              </div>

              {value.length > 1 && (
                <FontAwesomeIcon
                  className="release-icon"
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
            <Button
              size="sm"
              color="light"
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
            >
              <FontAwesomeIcon icon={faDownload}></FontAwesomeIcon>
            </Button>
          );
        },
      },
    ],
    [download, item]
  );

  const content = () => {
    if (results.isFetching) {
      return <LoadingIndicator animation="grow"></LoadingIndicator>;
    } else if (isStale) {
      return (
        <div className="px-4 py-5">
          <p className="mb-3 small">{item?.path ?? ""}</p>
          <Button color="primary" block onClick={search}>
            Start Search
          </Button>
        </div>
      );
    } else {
      return (
        <>
          <p className="mb-3 small">{item?.path ?? ""}</p>
          <PageTable
            emptyText="No Result"
            columns={columns}
            data={results.data ?? []}
          ></PageTable>
        </>
      );
    }
  };

  const title = useMemo(() => {
    let title = "Unknown";

    if (item) {
      if (item.sceneName) {
        title = item.sceneName;
      } else if (isMovie(item)) {
        title = item.title;
      } else {
        title = item.title;
      }
    }
    return `Search - ${title}`;
  }, [item]);

  const Modal = useModal({
    size: "xl",
    closeable: results.isFetching === false,
    onMounted: () => {
      // Cleanup the ID when user switches episode / movie
      if (itemId !== id) {
        setId(undefined);
      }
    },
  });

  const footer = (
    <Button color="light" hidden={isStale} onClick={search}>
      Search Again
    </Button>
  );

  return (
    <Modal title={title} footer={footer}>
      {content()}
    </Modal>
  );
}

export const MovieSearchModal = withModal<Props<Item.Movie>>(
  ManualSearchView,
  "movie-manual-search"
);
export const EpisodeSearchModal = withModal<Props<Item.Episode>>(
  ManualSearchView,
  "episode-manual-search"
);

const StateIcon: FunctionComponent<{ matches: string[]; dont: string[] }> = ({
  matches,
  dont,
}) => {
  let icon = faCheck;
  let color = "var(--success)";
  if (dont.length > 0) {
    icon = faInfoCircle;
    color = "var(--warning)";
  }

  const matchElements = useMemo(
    () =>
      matches.map((v, idx) => (
        <p key={`match-${idx}`} className="text-nowrap m-0">
          {v}
        </p>
      )),
    [matches]
  );
  const dontElements = useMemo(
    () =>
      dont.map((v, idx) => (
        <p key={`dont-${idx}`} className="text-nowrap m-0">
          {v}
        </p>
      )),
    [dont]
  );

  const popover = useMemo(
    () => (
      <Popover className="w-100" id="manual-search-matches-info">
        <Popover.Content>
          <Container fluid>
            <Row>
              <Col xs={6}>
                <FontAwesomeIcon
                  color="var(--success)"
                  icon={faCheck}
                ></FontAwesomeIcon>
                {matchElements}
              </Col>
              <Col xs={6}>
                <FontAwesomeIcon
                  color="var(--danger)"
                  icon={faTimes}
                ></FontAwesomeIcon>
                {dontElements}
              </Col>
            </Row>
          </Container>
        </Popover.Content>
      </Popover>
    ),
    [matchElements, dontElements]
  );

  return (
    <OverlayTrigger overlay={popover} placement={"left"}>
      <FontAwesomeIcon icon={icon} color={color}></FontAwesomeIcon>
    </OverlayTrigger>
  );
};
