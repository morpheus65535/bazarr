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
  description?: string;
};

const LibrarySelector: FunctionComponent<LibrarySelectorProps> = (props) => {
  const { libraryType, description, label, ...baseProps } = props;
  const { value, update, rest } = useBaseInput(baseProps);

  const { data: authData } = usePlexAuthValidationQuery();
  const isAuthenticated = Boolean(
    authData?.valid && authData?.auth_method === "oauth",
  );

  const { data: servers = [] } = usePlexServersQuery();
  const hasServers = servers.length > 0;

  const {
    data: libraries = [],
    isLoading,
    error,
  } = usePlexLibrariesQuery({
    enabled: isAuthenticated && hasServers,
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
          onChange={update}
          searchable
          clearable
          className={styles.selectField}
        />
        {error && (
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
