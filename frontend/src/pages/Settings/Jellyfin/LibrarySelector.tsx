import { FunctionComponent } from "react";
import { Alert, MultiSelect, Stack } from "@mantine/core";
import { useJellyfinLibrariesQuery } from "@/apis/hooks/jellyfin";
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
      <Alert color="brand" variant="light" className={styles.alertMessage}>
        Configure Jellyfin URL and API Key above to discover libraries.
      </Alert>
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
          className={styles.selectField}
        />
        {isLoading && (
          <Alert color="brand" variant="light" className={styles.alertMessage}>
            Fetching libraries from Jellyfin...
          </Alert>
        )}
        {error && !isLoading && (
          <Alert color="red" variant="light" className={styles.alertMessage}>
            Failed to load libraries from Jellyfin.
          </Alert>
        )}
        {!error && !isLoading && selectData.length === 0 && (
          <Alert color="gray" variant="light" className={styles.alertMessage}>
            No {libraryType === "movies" ? "movie" : "TV show"} libraries found.
          </Alert>
        )}
      </Stack>
    </div>
  );
};

export default LibrarySelector;
