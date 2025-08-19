import { FunctionComponent, useMemo } from "react";
import { Alert, Select, Stack, Text } from "@mantine/core";
import {
  usePlexAuthValidationQuery,
  usePlexLibrariesQuery,
} from "@/apis/hooks/plex";
import { BaseInput, useBaseInput } from "@/pages/Settings/utilities/hooks";
import styles from "@/pages/Settings/Plex/LibrarySelector.module.scss";

export type LibrarySelectorProps = BaseInput<string> & {
  label: string;
  libraryType: "movie" | "show";
  placeholder?: string;
  description?: string;
};

const LibrarySelector: FunctionComponent<LibrarySelectorProps> = (props) => {
  const { libraryType, placeholder, description, label, ...baseProps } = props;
  const { value, update, rest } = useBaseInput(baseProps);

  console.log(
    `[LibrarySelector-${libraryType}] Component render - value:`,
    value,
    "props:",
    { libraryType, label },
  );

  // Check if user is authenticated with OAuth
  const { data: authData } = usePlexAuthValidationQuery();
  const isAuthenticated = useMemo(() => {
    const result = Boolean(
      authData?.valid && authData?.auth_method === "oauth",
    );
    console.log(
      `[LibrarySelector-${libraryType}] Authentication check:`,
      result,
    );
    return result;
  }, [authData?.valid, authData?.auth_method, libraryType]);

  // Fetch libraries if authenticated
  const {
    data: libraries = [],
    isLoading,
    error,
  } = usePlexLibrariesQuery({
    enabled: isAuthenticated,
  });

  console.log(`[LibrarySelector-${libraryType}] Libraries data:`, {
    librariesCount: libraries.length,
    isLoading,
    hasError: !!error,
    isAuthenticated,
  });

  // Filter libraries by type and prepare select data
  const selectData = useMemo(() => {
    console.log(
      `[LibrarySelector-${libraryType}] Filtering libraries for type:`,
      libraryType,
    );
    const filtered = libraries.filter(
      (library) => library.type === libraryType,
    );
    const result = filtered.map((library) => ({
      value: library.title,
      label: `${library.title} (${library.count} items)`,
    }));
    console.log(`[LibrarySelector-${libraryType}] SelectData result:`, result);
    return result;
  }, [libraries, libraryType]);

  // If not authenticated, show message to use OAuth
  if (!isAuthenticated) {
    return (
      <Stack gap="xs" className={styles.librarySelector}>
        <Text fw={500} className={styles.labelText}>
          {label}
        </Text>
        <Alert color="brand" variant="light" className={styles.alertMessage}>
          Enable Plex OAuth above to automatically discover your libraries.
        </Alert>
      </Stack>
    );
  }

  // If loading
  if (isLoading) {
    return (
      <Stack gap="xs" className={styles.librarySelector}>
        <Text fw={500} className={styles.labelText}>
          {label}
        </Text>
        <Select
          {...rest}
          label={label}
          placeholder="Loading libraries..."
          data={[]}
          disabled
          className={styles.loadingField}
        />
      </Stack>
    );
  }

  // If error loading libraries
  if (error) {
    return (
      <Stack gap="xs" className={styles.librarySelector}>
        <Text fw={500} className={styles.labelText}>
          {label}
        </Text>
        <Alert color="red" variant="light" className={styles.alertMessage}>
          Failed to load libraries: {error.message}
        </Alert>
      </Stack>
    );
  }

  // If no libraries found of this type
  if (selectData.length === 0) {
    return (
      <Stack gap="xs" className={styles.librarySelector}>
        <Text fw={500} className={styles.labelText}>
          {label}
        </Text>
        <Alert color="gray" variant="light" className={styles.alertMessage}>
          No {libraryType} libraries found on your Plex server.
        </Alert>
      </Stack>
    );
  }

  return (
    <div className={styles.librarySelector}>
      <Select
        {...rest}
        label={label}
        placeholder={placeholder || `Select ${libraryType} library...`}
        data={selectData}
        description={description}
        value={value || ""}
        onChange={(newValue) => {
          console.log(
            `[LibrarySelector-${libraryType}] onChange called with:`,
            newValue,
            "current value:",
            value,
          );
          // Prevent deselection - if user clicks on already selected option, keep current value
          if (newValue !== null) {
            console.log(
              `[LibrarySelector-${libraryType}] Calling update with:`,
              newValue,
            );
            update(newValue);
          } else {
            console.log(
              `[LibrarySelector-${libraryType}] Prevented null update`,
            );
          }
        }}
        allowDeselect={false}
        className={styles.selectField}
        comboboxProps={{
          withinPortal: false,
          position: "bottom-start",
          offset: 0,
          middlewares: {
            flip: false,
            shift: false,
            inline: false,
          },
          positionDependencies: [],
        }}
      />
    </div>
  );
};

export default LibrarySelector;
