import {
  faCaretDown,
  faCheck,
  faDownload,
  faInfoCircle,
  faTimes,
} from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import React, {
  FunctionComponent,
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";
import {
  Badge,
  Button,
  Col,
  Collapse,
  Container,
  OverlayTrigger,
  Popover,
  Row,
} from "react-bootstrap";
import { Column } from "react-table";
import {
  BaseModal,
  BaseModalProps,
  LanguageText,
  LoadingIndicator,
  PageTable,
  useModalPayload,
} from "..";
import { dispatchTask } from "../../@modules/task";
import { createTask } from "../../@modules/task/utilities";
import { ProvidersApi } from "../../apis";
import { GetItemId, isMovie } from "../../utilities";
import "./msmStyle.scss";

type SupportType = Item.Movie | Item.Episode;

enum SearchState {
  Ready,
  Searching,
  Finished,
}

interface Props<T extends SupportType> {
  download: (item: T, result: SearchResultType) => Promise<void>;
}

export function ManualSearchModal<T extends SupportType>(
  props: Props<T> & BaseModalProps
) {
  const { download, ...modal } = props;

  const [result, setResult] = useState<SearchResultType[]>([]);
  const [searchState, setSearchState] = useState(SearchState.Ready);

  const item = useModalPayload<T>(modal.modalKey);

  const search = useCallback(async () => {
    if (item) {
      setSearchState(SearchState.Searching);
      let results: SearchResultType[] = [];
      if (isMovie(item)) {
        results = await ProvidersApi.movies(item.radarrId);
      } else {
        results = await ProvidersApi.episodes(item.sonarrEpisodeId);
      }
      setResult(results);
      setSearchState(SearchState.Finished);
    }
  }, [item]);

  useEffect(() => {
    if (item !== null) {
      setSearchState(SearchState.Ready);
    }
  }, [item]);

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
            <Badge text="secondary">
              <LanguageText text={lang}></LanguageText>
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

          const cls = [
            "release-container",
            "d-flex",
            "justify-content-between",
            "align-items-center",
          ];

          if (value.length > 1) {
            cls.push("release-multi");
          }

          return (
            <div className={cls.join(" ")} onClick={() => setOpen((o) => !o)}>
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
              variant="light"
              disabled={item === null}
              onClick={() => {
                if (!item) return;

                const id = GetItemId(item);
                const task = createTask(item.title, id, download, item, result);
                dispatchTask(
                  "Downloading subtitles...",
                  [task],
                  "Downloading..."
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

  const content = useMemo<JSX.Element>(() => {
    if (searchState === SearchState.Ready) {
      return (
        <div className="px-4 py-5">
          <p className="mb-3 small">{item?.path ?? ""}</p>
          <Button variant="primary" onClick={search}>
            Start Search
          </Button>
        </div>
      );
    } else if (searchState === SearchState.Searching) {
      return <LoadingIndicator animation="grow"></LoadingIndicator>;
    } else {
      return (
        <React.Fragment>
          <p className="mb-3 small">{item?.path ?? ""}</p>
          <PageTable
            emptyText="No Result"
            columns={columns}
            data={result}
          ></PageTable>
        </React.Fragment>
      );
    }
  }, [searchState, columns, result, search, item?.path]);

  const footer = useMemo(
    () => (
      <Button
        variant="light"
        hidden={searchState !== SearchState.Finished}
        onClick={search}
      >
        Search Again
      </Button>
    ),
    [searchState, search]
  );

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

  return (
    <BaseModal
      closeable={searchState !== SearchState.Searching}
      size="xl"
      title={title}
      footer={footer}
      {...modal}
    >
      {content}
    </BaseModal>
  );
}

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
        <Popover.Body>
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
        </Popover.Body>
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
