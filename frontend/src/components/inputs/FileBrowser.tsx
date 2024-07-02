import { FunctionComponent, useEffect, useMemo, useRef, useState } from "react";
import {
  Autocomplete,
  AutocompleteProps,
  ComboboxItem,
  OptionsFilter,
} from "@mantine/core";
import { faFolder } from "@fortawesome/free-regular-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { useFileSystem } from "@/apis/hooks";

// TODO: use fortawesome icons
const backKey = "⏎ Back";

function getLastSeparator(path: string): number {
  let idx = path.lastIndexOf("/");
  if (idx === -1) {
    idx = path.lastIndexOf("\\");
  }
  return idx;
}

function extractPath(raw: string) {
  if (raw.endsWith("/") || raw.endsWith("\\")) {
    return raw;
  } else {
    const idx = getLastSeparator(raw);
    return raw.slice(0, idx + 1);
  }
}

export type FileBrowserProps = Omit<AutocompleteProps, "data"> & {
  type: "sonarr" | "radarr" | "bazarr";
};

type FileTreeItem = {
  value: string;
  item?: FileTree;
};

export const FileBrowser: FunctionComponent<FileBrowserProps> = ({
  defaultValue,
  type,
  onChange,
  ...props
}) => {
  const [isShow, setIsShow] = useState(false);
  const [value, setValue] = useState(defaultValue ?? "");
  const [path, setPath] = useState(() => extractPath(value));

  const { data: tree } = useFileSystem(type, path, isShow);

  const data = useMemo<FileTreeItem[]>(
    () => [
      { value: backKey },
      ...(tree?.map((v) => ({
        value: v.path,
        item: v,
      })) ?? []),
    ],
    [tree],
  );

  const parent = useMemo(() => {
    const idx = getLastSeparator(path.slice(0, -1));
    return path.slice(0, idx + 1);
  }, [path]);

  useEffect(() => {
    if (value === path) {
      return;
    }

    const newPath = extractPath(value);
    if (newPath !== path) {
      setPath(newPath);
      onChange && onChange(newPath);
    }
  }, [path, value, onChange]);

  const ref = useRef<HTMLInputElement>(null);

  const optionsFilter: OptionsFilter = ({ options, search }) => {
    return (options as ComboboxItem[]).filter((option) => {
      if (search === backKey) {
        return true;
      }

      return option.value.includes(search);
    });
  };

  return (
    <Autocomplete
      {...props}
      ref={ref}
      leftSection={<FontAwesomeIcon icon={faFolder}></FontAwesomeIcon>}
      placeholder="Click to start"
      data={data}
      value={value}
      // Temporary solution of infinite dropdown items, fix later
      limit={NaN}
      maxDropdownHeight={240}
      filter={optionsFilter}
      onChange={(val) => {
        if (val !== backKey) {
          setValue(val);
        } else {
          setValue(parent);
        }
      }}
      onFocus={() => setIsShow(true)}
      onBlur={() => setIsShow(false)}
    ></Autocomplete>
  );
};
