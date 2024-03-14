import { Action, FileBrowser, SimpleTable } from "@/components";
import { useArrayAction } from "@/utilities";
import { faArrowCircleRight, faTrash } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { Button } from "@mantine/core";
import { capitalize } from "lodash";
import { FunctionComponent, useCallback, useMemo } from "react";
import { Column } from "react-table";
import {
  moviesEnabledKey,
  pathMappingsKey,
  pathMappingsMovieKey,
  seriesEnabledKey,
} from "../keys";
import { useFormActions } from "../utilities/FormValues";
import { useSettingValue } from "../utilities/hooks";
import { Message } from "./Message";

type SupportType = "sonarr" | "radarr";

function getSupportKey(type: SupportType) {
  if (type === "sonarr") {
    return pathMappingsKey;
  } else {
    return pathMappingsMovieKey;
  }
}

function getEnabledKey(type: SupportType) {
  if (type === "sonarr") {
    return seriesEnabledKey;
  } else {
    return moviesEnabledKey;
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
  const items = useSettingValue<[string, string][]>(key);

  const enabledKey = getEnabledKey(type);
  const enabled = useSettingValue<boolean>(enabledKey, { original: true });

  const { setValue } = useFormActions();

  const updateRow = useCallback(
    (newItems: PathMappingItem[]) => {
      setValue(
        newItems.map((v) => [v.from, v.to]),
        key,
      );
    },
    [key, setValue],
  );

  const addRow = useCallback(() => {
    if (items) {
      const newItems = [...items, ["", ""]];
      setValue(newItems, key);
    }
  }, [items, key, setValue]);

  const data = useMemo<PathMappingItem[]>(
    () => items?.map((v) => ({ from: v[0], to: v[1] })) ?? [],
    [items],
  );

  const action = useArrayAction<PathMappingItem>((fn) => {
    updateRow(fn(data));
  });

  const columns = useMemo<Column<PathMappingItem>[]>(
    () => [
      {
        Header: capitalize(type),
        accessor: "from",
        Cell: ({ value, row: { original, index } }) => {
          return (
            <FileBrowser
              type={type}
              defaultValue={value}
              onChange={(path) => {
                action.mutate(index, { ...original, from: path });
              }}
            ></FileBrowser>
          );
        },
      },
      {
        id: "arrow",
        Cell: () => (
          <FontAwesomeIcon icon={faArrowCircleRight}></FontAwesomeIcon>
        ),
      },
      {
        Header: "Bazarr",
        accessor: "to",
        Cell: ({ value, row: { original, index } }) => {
          return (
            <FileBrowser
              defaultValue={value}
              type="bazarr"
              onChange={(path) => {
                action.mutate(index, { ...original, to: path });
              }}
            ></FileBrowser>
          );
        },
      },
      {
        id: "action",
        accessor: "to",
        Cell: ({ row: { index } }) => {
          return (
            <Action
              label="Remove"
              icon={faTrash}
              onClick={() => action.remove(index)}
            ></Action>
          );
        },
      },
    ],
    [action, type],
  );

  if (enabled) {
    return (
      <>
        <SimpleTable
          tableStyles={{ emptyText: "No mapping" }}
          columns={columns}
          data={data}
        ></SimpleTable>
        <Button fullWidth color="light" onClick={addRow}>
          Add
        </Button>
      </>
    );
  } else {
    return (
      <Message>
        Path Mappings will be available after staged changes are saved
      </Message>
    );
  }
};
