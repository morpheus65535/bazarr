import React, {
  FunctionComponent,
  useCallback,
  useMemo,
  useState,
} from "react";
import {
  usePayload,
  BasicModal,
  BasicModalProps,
  BasicTable,
  AsyncButton,
  LoadingIndicator,
} from "..";
import { Column } from "react-table";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import {
  faDownload,
  faCheck,
  faTimes,
  faInfoCircle,
} from "@fortawesome/free-solid-svg-icons";
import {
  Badge,
  Button,
  Popover,
  OverlayTrigger,
  Container,
  Row,
  Col,
  Dropdown,
} from "react-bootstrap";
import { useWhenModalShow } from "./provider";

export interface ManualSearchPayload {
  title: string;
  id: number;
  promise: (id: number) => Promise<ManualSearchResult[]>;
}

interface Props {
  onSelect: (id: number, result: ManualSearchResult) => Promise<void>;
  onDownload?: () => void;
}

export const ManualSearchModal: FunctionComponent<Props & BasicModalProps> = (
  props
) => {
  const { onSelect, onDownload, ...modal } = props;

  const [result, setResult] = useState<ManualSearchResult[]>([]);
  const [searching, setSearch] = useState(false);
  const [start, setStart] = useState(false);

  const payload = usePayload<ManualSearchPayload>(modal.modalKey);

  const search = useCallback(() => {
    if (payload) {
      const { id, promise } = payload;
      setStart(true);
      setSearch(true);
      promise(id)
        .then((data) => setResult(data))
        .finally(() => setSearch(false));
    }
  }, [payload]);

  const [lastId, setId] = useState<number | undefined>(undefined);

  useWhenModalShow(modal.modalKey, () => {
    const id = payload?.id;
    if (id !== lastId) {
      cancel();
      setId(id);
    }
  });

  const cancel = useCallback(() => {
    setStart(false);
    setSearch(false);
  }, []);

  const columns = useMemo<Column<ManualSearchResult>[]>(
    () => [
      {
        accessor: "subtitle",
        Cell: (row) => {
          const result = row.row.original;
          return (
            <AsyncButton
              size="sm"
              variant="light"
              promise={() => onSelect(payload!.id, result)}
              onSuccess={onDownload}
            >
              <FontAwesomeIcon icon={faDownload}></FontAwesomeIcon>
            </AsyncButton>
          );
        },
      },
      {
        Header: "Score",
        accessor: (d) => `${d.score}%`,
      },
      {
        accessor: "language",
        Cell: (row) => <Badge variant="secondary">{row.value}</Badge>,
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
                  className="dropdown-hidden text-dark opacity-100"
                  variant={value.length === 1 ? "link" : "light"}
                >
                  {display}
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
    ],
    [onSelect, payload, onDownload]
  );

  const content = useMemo<JSX.Element>(() => {
    if (!start) {
      return (
        <div className="px-4 py-5">
          <Button variant="primary" block onClick={search}>
            Start Search
          </Button>
        </div>
      );
    } else if (searching) {
      return <LoadingIndicator animation="grow"></LoadingIndicator>;
    } else {
      return (
        <BasicTable
          emptyText="No Result"
          columns={columns}
          data={result}
        ></BasicTable>
      );
    }
  }, [start, searching, columns, result, search]);

  const footer = useMemo(
    () => (
      <Button variant="danger" disabled={!start} onClick={cancel}>
        Reset
      </Button>
    ),
    [start, cancel]
  );

  return (
    <BasicModal
      size={start ? "xl" : "lg"}
      title={`Search - ${payload?.title ?? "Unknown"}`}
      footer={footer}
      {...modal}
    >
      {content}
    </BasicModal>
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
    () => matches.map((v) => <p className="text-nowrap m-0">{v}</p>),
    [matches]
  );
  const dontElements = useMemo(
    () => dont.map((v) => <p className="text-nowrap m-0">{v}</p>),
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
