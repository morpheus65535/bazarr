import { FunctionComponent } from "react";
import { MultiSelect, Stack } from "@mantine/core";
import { useJellyfinLibrariesQuery } from "@/apis/hooks/jellyfin";
import { Message } from "@/pages/Settings/components";
import { BaseInput, useBaseInput } from "@/pages/Settings/utilities/hooks";
import { useSettingValue } from "@/pages/Settings/utilities/hooks";
import styles from "./LibrarySelector.module.scss";

export type LibrarySelectorProps = BaseInput<string[]> & {
  label: string;
  libraryType: "movies" | "tvshows";
  settingKeyIds?: string;
  description?: string;
};

const LibrarySelector: FunctionComponent<LibrarySelectorProps> = (props) => {
  const { libraryType, description, label, settingKeyIds, ...baseProps } =
    props;
  const { value, update, rest } = useBaseInput(baseProps);

  const idsInput = useBaseInput({
    settingKey: settingKeyIds || "",
  });

  const jellyfinUrl = useSettingValue<string>("settings-jellyfin-url");
  const jellyfinApikey = useSettingValue<string>("settings-jellyfin-apikey");
  const isConfigured = Boolean(jellyfinUrl && jellyfinApikey);

  const {
    data: librariesData,
    isLoading,
    error,
  } = useJellyfinLibrariesQuery(
    isConfigured,
    jellyfinUrl ?? undefined,
    jellyfinApikey ?? undefined,
  );

  const libraries = librariesData ?? [];
  const filtered = libraries.filter((lib) => lib.type === libraryType);
  const normalizedValue = Array.isArray(value) ? value : value ? [value] : [];

  const availableLibraries = filtered.map((lib) => lib.name);
  const staleLibraries = normalizedValue.filter(
    (name) => !availableLibraries.includes(name),
  );

  const selectData = [
    ...filtered.map((library) => ({
      value: library.name,
      label: library.name,
    })),
    ...staleLibraries.map((name) => ({
      value: name,
      label: `${name} (unavailable)`,
    })),
  ];

  const handleChange = (selectedNames: string[]) => {
    update(selectedNames);

    if (settingKeyIds) {
      const selectedIds = filtered
        .filter((lib) => selectedNames.includes(lib.name))
        .map((lib) => lib.id);
      idsInput.update(selectedIds);
    }
  };

  if (!isConfigured) {
    return (
      <Message type="warning">
        Configure Jellyfin URL and API Key above to discover libraries.
      </Message>
    );
  }

  return (
    <div className={styles.librarySelector}>
      <Stack gap="xs">
        <MultiSelect
          {...rest}
          label={label}
          description={description}
          data={selectData}
          value={normalizedValue}
          onChange={handleChange}
          searchable
          clearable
        />
        {isLoading && <Message>Fetching libraries from Jellyfin...</Message>}
        {error && !isLoading && (
          <Message type="warning">
            Failed to load libraries from Jellyfin.
          </Message>
        )}
        {!error && !isLoading && selectData.length === 0 && (
          <Message>
            No {libraryType === "movies" ? "movie" : "TV show"} libraries found.
          </Message>
        )}
      </Stack>
    </div>
  );
};

export default LibrarySelector;
