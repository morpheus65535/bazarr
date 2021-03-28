import {
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
  Container,
  Dropdown,
  OverlayTrigger,
  Popover,
  Row,
} from "react-bootstrap";
import { Column } from "react-table";
import {
  AsyncButton,
  BaseModal,
  BaseModalProps,
  LanguageText,
  LoadingIndicator,
  PageTable,
  usePayload,
} from "..";
import { ProvidersApi } from "../../apis";
import { isMovie } from "../../utilites";

type SupportType = Item.Movie | Item.Episode;

interface Props {
  onSelect: (item: SupportType, result: SearchResultType) => Promise<void>;
  onDownload?: () => void;
}

export const ManualSearchModal: FunctionComponent<Props & BaseModalProps> = (
  props
) => {
  const { onSelect, onDownload, ...modal } = props;

  const [result, setResult] = useState<SearchResultType[]>([]);
  const [searching, setSearch] = useState(false);
  const [start, setStart] = useState(false);

  const item = usePayload<SupportType>(modal.modalKey);

  const search = useCallback(() => {
    if (item) {
      setStart(true);
      setSearch(true);
      let promise: Promise<SearchResultType[]>;
      if (isMovie(item)) {
        promise = ProvidersApi.movies(item.radarrId);
      } else {
        promise = ProvidersApi.episodes(item.sonarrEpisodeId);
      }
      promise.then((data) => setResult(data)).finally(() => setSearch(false));
    }
  }, [item]);

  const reset = useCallback(() => {
    setStart(false);
    setSearch(false);
  }, []);

  useEffect(() => {
    if (item) {
      reset();
    }
  }, [item, reset]);

  const columns = useMemo<Column<SearchResultType>[]>(
    () => [
      {
        Header: "Score",
        accessor: (d) => `${d.score}%`,
      },
      {
        accessor: "language",
        Cell: ({ row: { original }, value }) => {
          const lang: Language = {
            code2: value,
            hi: original.hearing_impaired === "True",
            forced: original.forced === "True",
            name: "",
          };
          return (
            <Badge variant="secondary">
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

          const items = useMemo(
            () =>
              value.slice(1).map((v, idx) => (
                <Dropdown.Item key={idx} disabled className="text-dark">
                  {v}
                </Dropdown.Item>
              )),
            [value]
          );

          if (value.length !== 0) {
            const display = value[0];
            return (
              <Dropdown>
                <Dropdown.Toggle
                  disabled={value.length === 1}
                  className="dropdown-hidden text-dark dropdown-toggle-wrap"
                  variant={value.length === 1 ? "link" : "light"}
                >
                  <span>{display}</span>
                </Dropdown.Toggle>
                <Dropdown.Menu>{items}</Dropdown.Menu>
              </Dropdown>
            );
          } else {
            return "Cannot get release info";
          }
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
        Cell: ({ row, externalUpdate }) => {
          const result = row.original;
          return (
            <AsyncButton
              size="sm"
              variant="light"
              noReset
              promise={() => onSelect(item!, result)}
              onSuccess={() => externalUpdate && externalUpdate(row)}
            >
              <FontAwesomeIcon icon={faDownload}></FontAwesomeIcon>
            </AsyncButton>
          );
        },
      },
    ],
    [onSelect, item]
  );

  const content = useMemo<JSX.Element>(() => {
    if (!start) {
      return (
        <div className="px-4 py-5">
          <p className="mb-3 small">{item?.path ?? ""}</p>
          <Button variant="primary" block onClick={search}>
            Start Search
          </Button>
        </div>
      );
    } else if (searching) {
      return <LoadingIndicator animation="grow"></LoadingIndicator>;
    } else {
      return (
        <React.Fragment>
          <p className="mb-3 small">{item?.path ?? ""}</p>
          <PageTable
            emptyText="No Result"
            columns={columns}
            data={result}
            externalUpdate={onDownload}
          ></PageTable>
        </React.Fragment>
      );
    }
  }, [start, searching, columns, result, search, item?.path, onDownload]);

  const footer = useMemo(
    () => (
      <Button variant="light" disabled={!start} onClick={reset}>
        Reset
      </Button>
    ),
    [start, reset]
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
      closeable={!searching}
      size="xl"
      title={title}
      footer={footer}
      {...modal}
    >
      {content}
    </BaseModal>
  );
};

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
      <Popover id="manual-search-matches-info">
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
    <OverlayTrigger overlay={popover}>
      <FontAwesomeIcon icon={icon} color={color}></FontAwesomeIcon>
    </OverlayTrigger>
  );
};
