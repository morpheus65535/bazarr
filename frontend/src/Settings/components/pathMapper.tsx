import { faArrowCircleRight, faTrash } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { capitalize, isArray } from "lodash";
import React, { FunctionComponent, useCallback, useMemo } from "react";
import { Button } from "react-bootstrap";
import { Column, TableUpdater } from "react-table";
import { FilesApi } from "../../apis";
import { ActionIcon, FileBrowser, SimpleTable } from "../../components";
import { pathMappingsKey, pathMappingsMovieKey } from "../keys";
import { useLatest } from "./hooks";
import { useLocalUpdater } from "./provider";

type SupportType = "sonarr" | "radarr";

function getSupportKey(type: SupportType) {
  if (type === "sonarr") {
    return pathMappingsKey;
  } else {
    return pathMappingsMovieKey;
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

  const update = useLocalUpdater();

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

  const updateCell = useCallback<TableUpdater<PathMappingItem>>(
    (row, item?: PathMappingItem) => {
      const newItems = [...data];
      if (item) {
        newItems[row.index] = item;
      } else {
        newItems.splice(row.index, 1);
      }
      updateRow(newItems);
    },
    [data, updateRow]
  );

  const columns = useMemo<Column<PathMappingItem>[]>(
    () => [
      {
        Header: capitalize(type),
        accessor: "from",
        Cell: ({ value, row, update }) => (
          <FileBrowser
            drop="up"
            defaultValue={value}
            load={request}
            onChange={(path) => {
              const newItem = { ...row.original };
              newItem.from = path;
              update && update(row, newItem);
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
        Cell: ({ value, row, update }) => (
          <FileBrowser
            drop="up"
            defaultValue={value}
            load={(path) => FilesApi.bazarr(path)}
            onChange={(path) => {
              const newItem = { ...row.original };
              newItem.to = path;
              update && update(row, newItem);
            }}
          ></FileBrowser>
        ),
      },
      {
        id: "action",
        accessor: "to",
        Cell: ({ row, update }) => (
          <ActionIcon
            icon={faTrash}
            onClick={() => {
              update && update(row);
            }}
          ></ActionIcon>
        ),
      },
    ],
    [type, request]
  );
  return (
    <React.Fragment>
      <SimpleTable
        emptyText="No Mapping"
        responsive={false}
        columns={columns}
        data={data}
        update={updateCell}
      ></SimpleTable>
      <Button block variant="light" onClick={addRow}>
        Add
      </Button>
    </React.Fragment>
  );
};
