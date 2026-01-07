import { FunctionComponent } from "react";
import { Alert, MultiSelect, Stack } from "@mantine/core";
import {
  usePlexAuthValidationQuery,
  usePlexLibrariesQuery,
  usePlexServersQuery,
} from "@/apis/hooks/plex";
import { BaseInput, useBaseInput } from "@/pages/Settings/utilities/hooks";
import styles from "@/pages/Settings/Plex/LibrarySelector.module.scss";

export type LibrarySelectorProps = BaseInput<string[]> & {
  label: string;
  libraryType: "movie" | "show";
  settingKeyIds?: string;
  description?: string;
};

const LibrarySelector: FunctionComponent<LibrarySelectorProps> = (props) => {
  const { libraryType, description, label, settingKeyIds, ...baseProps } =
    props;
  const { value, update, rest } = useBaseInput(baseProps);

  // Hook for storing library IDs alongside names
  const idsInput = useBaseInput({
    settingKey: settingKeyIds || "",
    // Provide a default value getter that returns empty array
  });

  const { data: authData } = usePlexAuthValidationQuery();
  const isAuthenticated = Boolean(
    authData?.valid && authData?.auth_method === "oauth",
  );

  const { data: servers = [] } = usePlexServersQuery();
  const hasServers = servers.length > 0;

  // Check if a server has been selected (required for library fetching)
  const selectedServer = servers.find((server) => server.bestConnection);
  const hasSelectedServer = Boolean(selectedServer);

  const {
    data: libraries = [],
    isLoading,
    error,
  } = usePlexLibrariesQuery({
    enabled: isAuthenticated && hasServers && hasSelectedServer,
  });

  const filtered = libraries.filter((library) => library.type === libraryType);
  const normalizedValue = Array.isArray(value) ? value : value ? [value] : [];

  // Add stale libraries to dropdown data
  const availableLibraries = filtered.map((lib) => lib.title);
  const staleLibraries = normalizedValue.filter(
    (name) => !availableLibraries.includes(name),
  );

  const selectData = [
    ...filtered.map((library) => ({
      value: library.title,
      label: `${library.title} (${library.count} items)`,
    })),
    ...staleLibraries.map((name) => ({
      value: name,
      label: `${name} (unavailable)`,
    })),
  ];

  // Handle selection change - update both names and IDs
  const handleChange = (selectedTitles: string[]) => {
    update(selectedTitles); // Update library names (e.g., ["4K Movies", "Movies"])

    // Also update the IDs array if settingKeyIds is provided
    if (settingKeyIds) {
      const selectedIds = filtered
        .filter((lib) => selectedTitles.includes(lib.title))
        .map((lib) => lib.key);
      idsInput.update(selectedIds); // Update library IDs (e.g., ["1", "3"])
    }
  };

  if (!isAuthenticated) {
    return (
      <Alert color="brand" variant="light" className={styles.alertMessage}>
        Enable Plex OAuth above to automatically discover your libraries.
      </Alert>
    );
  }

  if (!hasServers) {
    return (
      <Alert color="brand" variant="light" className={styles.alertMessage}>
        Waiting for server connections to be tested...
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
            Fetching libraries... This might take a moment.
          </Alert>
        )}
        {error && !isLoading && (
          <Alert color="red" variant="light" className={styles.alertMessage}>
            Failed to load libraries from Plex. Saved selections shown above.
          </Alert>
        )}
        {!error && !isLoading && selectData.length === 0 && (
          <Alert color="gray" variant="light" className={styles.alertMessage}>
            No {libraryType} libraries found on your Plex server.
          </Alert>
        )}
      </Stack>
    </div>
  );
};

export default LibrarySelector;
