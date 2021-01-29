import React, {
  FunctionComponent,
  useCallback,
  useMemo,
  useState,
} from "react";
import BasicModal, { BasicModalProps } from "./BasicModal";
import { Badge, ButtonGroup, Dropdown } from "react-bootstrap";
import { Column } from "react-table";
import { BasicTable, ActionIcon, ActionIconItem } from "..";
import { SubtitlesApi } from "../../apis";
import { usePayload } from "./provider";
import {
  faClock,
  faCode,
  faDeaf,
  faExchangeAlt,
  faFilm,
  faImage,
  faMagic,
  faPaintBrush,
  faPlay,
  faTextHeight,
} from "@fortawesome/free-solid-svg-icons";
import { isMovie } from "../../utilites";

type SupportType = Episode | Movie;

interface Props {
  item?: SupportType;
}

const Table: FunctionComponent<Props> = ({ item }) => {
  const submitAction = useCallback((action: string, sub: Subtitle) => {
    if (sub.path) {
      setUpdate(true);
      setActive(sub.path);
      SubtitlesApi.modify(action, sub.code2, sub.path).finally(() => {
        setUpdate(false);
        setActive(undefined);
      });
    }
  }, []);

  const [updating, setUpdate] = useState<boolean>(false);
  const [active, setActive] = useState<string | undefined>(undefined);

  const syncSubtitle = useCallback(
    (sub: Subtitle) => {
      if (sub.path && item) {
        const [type, id]: ["movie" | "episode", number] = isMovie(item)
          ? ["movie", item.radarrId]
          : ["episode", item.sonarrEpisodeId];

        setUpdate(true);
        setActive(sub.path);
        SubtitlesApi.sync(sub.code2, sub.path, type, id).finally(() => {
          setUpdate(false);
          setActive(undefined);
        });
      }
    },
    [item]
  );

  const columns: Column<Subtitle>[] = useMemo<Column<Subtitle>[]>(
    () => [
      {
        accessor: "name",
        Cell: (row) => <Badge variant="secondary">{row.value}</Badge>,
      },
      {
        Header: "File Name",
        accessor: "path",
        Cell: (row) => {
          const path = row.value!;

          let idx = path.lastIndexOf("/");

          if (idx === -1) {
            idx = path.lastIndexOf("\\");
          }

          if (idx !== -1) {
            return path.slice(idx + 1);
          } else {
            return path;
          }
        },
      },
      {
        Header: "Tools",
        accessor: "code2",
        Cell: (row) => {
          const sub = row.row.original;

          const isActive = sub.path !== null && sub.path === active;

          return (
            <Dropdown
              as={ButtonGroup}
              onSelect={(k) => k && submitAction(k, sub)}
            >
              <ActionIcon
                loading={isActive}
                disabled={updating}
                icon={faPlay}
                onClick={() => syncSubtitle(sub)}
              >
                Sync
              </ActionIcon>
              <Dropdown.Toggle
                disabled={updating}
                split
                variant="light"
                size="sm"
                className="px-2"
              ></Dropdown.Toggle>
              <Dropdown.Menu>
                <Dropdown.Item eventKey="remove_HI">
                  <ActionIconItem icon={faDeaf}>Remove HI Tags</ActionIconItem>
                </Dropdown.Item>
                <Dropdown.Item eventKey="remove_tags">
                  <ActionIconItem icon={faCode}>
                    Remove Style Tags
                  </ActionIconItem>
                </Dropdown.Item>
                <Dropdown.Item eventKey="OCR_fixes">
                  <ActionIconItem icon={faImage}>OCR Fixes</ActionIconItem>
                </Dropdown.Item>
                <Dropdown.Item eventKey="common">
                  <ActionIconItem icon={faMagic}>Common Fixes</ActionIconItem>
                </Dropdown.Item>
                <Dropdown.Item eventKey="fix_uppercase">
                  <ActionIconItem icon={faTextHeight}>
                    Fix Uppercase
                  </ActionIconItem>
                </Dropdown.Item>
                <Dropdown.Item eventKey="reverse_rtl">
                  <ActionIconItem icon={faExchangeAlt}>
                    Reverse RTL
                  </ActionIconItem>
                </Dropdown.Item>
                <Dropdown.Item>
                  <ActionIconItem icon={faPaintBrush}>Add Color</ActionIconItem>
                </Dropdown.Item>
                <Dropdown.Item>
                  <ActionIconItem icon={faFilm}>
                    Change Frame Rate
                  </ActionIconItem>
                </Dropdown.Item>
                <Dropdown.Item>
                  <ActionIconItem icon={faClock}>Adjust Times</ActionIconItem>
                </Dropdown.Item>
              </Dropdown.Menu>
            </Dropdown>
          );
        },
      },
    ],
    [submitAction, updating, syncSubtitle, active]
  );

  const data: Subtitle[] = useMemo<Subtitle[]>(
    () => item?.subtitles.filter((val) => val.path !== null) ?? [],
    [item]
  );

  return (
    <BasicTable
      emptyText="No External Subtitles Found"
      responsive={false}
      columns={columns}
      data={data}
    ></BasicTable>
  );
};

const Tools: FunctionComponent<Props & BasicModalProps> = (props) => {
  const item = usePayload<SupportType>(props.modalKey);
  return (
    <BasicModal title={`Tools - ${item?.title ?? ""}`} {...props}>
      <Table item={item} {...props}></Table>
    </BasicModal>
  );
};

export default Tools;
