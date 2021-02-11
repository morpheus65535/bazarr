import { faArrowCircleRight, faTrash } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { capitalize, isArray } from "lodash";
import React, { FunctionComponent, useCallback, useMemo } from "react";
import { Button } from "react-bootstrap";
import { Column } from "react-table";
import { FilesApi } from "../../apis";
import { ActionIcon, BasicTable, FileBrowser } from "../../components";
import { tableUseOriginals } from "../../utilites";
import { useLatest } from "./hooks";
import { useUpdate } from "./provider";

type SupportType = "sonarr" | "radarr";

function getSupportKey(type: SupportType) {
  if (type === "sonarr") {
    return "settings-general-path_mappings";
  } else {
    return "settings-general-path_mappings_movie";
  }
}

interface PathMappingItem {
  from: string;
  to: string;
}

interface TableProps {
  type: SupportType;
}

export const PathMappingTable: FunctionComponent<TableProps> = ({ type }) => {
  const key = getSupportKey(type);

  const items = useLatest<[string, string][]>(key, isArray);

  const update = useUpdate();

  const updateRow = useCallback(
    (newItems: PathMappingItem[]) => {
      update(
        newItems.map((v) => [v.from, v.to]),
        key
      );
    },
    [key, update]
  );

  const addRow = useCallback(() => {
    if (items) {
      const newItems = [...items, ["", ""]];
      update(newItems, key);
    }
  }, [items, key, update]);

  const data = useMemo<PathMappingItem[]>(
    () => items?.map((v) => ({ from: v[0], to: v[1] })) ?? [],
    [items]
  );

  const request = useMemo(() => {
    if (type === "sonarr") {
      return (path: string) => FilesApi.sonarr(path);
    } else {
      return (path: string) => FilesApi.radarr(path);
    }
  }, [type]);

  const columns = useMemo<Column<PathMappingItem>[]>(
    () => [
      {
        Header: capitalize(type),
        accessor: "from",
        Cell: ({ value, row, rows }) => (
          <FileBrowser
            defaultValue={value}
            load={request}
            onBlur={(path) => {
              const newItems = tableUseOriginals(rows);
              newItems[row.index].from = path;
              updateRow(newItems);
            }}
          ></FileBrowser>
        ),
      },
      {
        id: "arrow",
        className: "text-center",
        Cell: () => (
          <FontAwesomeIcon icon={faArrowCircleRight}></FontAwesomeIcon>
        ),
      },
      {
        Header: "Bazarr",
        accessor: "to",
        Cell: ({ value, row, rows }) => (
          <FileBrowser
            defaultValue={value}
            load={(path) => FilesApi.bazarr(path)}
            onBlur={(path) => {
              const newItems = tableUseOriginals(rows);
              newItems[row.index].to = path;
              updateRow(newItems);
            }}
          ></FileBrowser>
        ),
      },
      {
        id: "action",
        accessor: "to",
        Cell: ({ row, rows }) => (
          <ActionIcon
            icon={faTrash}
            onClick={() => {
              const newItems = tableUseOriginals(rows);
              newItems.splice(row.index, 1);
              updateRow(newItems);
            }}
          ></ActionIcon>
        ),
      },
    ],
    [type, request, updateRow]
  );
  return (
    <React.Fragment>
      <BasicTable
        emptyText="No Mapping"
        responsive={false}
        showPageControl={false}
        columns={columns}
        data={data}
      ></BasicTable>
      <Button block variant="light" onClick={addRow}>
        Add
      </Button>
    </React.Fragment>
  );
};
