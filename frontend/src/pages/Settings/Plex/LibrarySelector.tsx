import { FunctionComponent } from "react";
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

  // Check if user is authenticated with OAuth
  const { data: authData } = usePlexAuthValidationQuery();
  const isAuthenticated = Boolean(
    authData?.valid && authData?.auth_method === "oauth",
  );

  // Fetch libraries if authenticated
  const {
    data: libraries = [],
    isLoading,
    error,
  } = usePlexLibrariesQuery({
    enabled: isAuthenticated,
  });

  // Filter libraries by type and prepare select data
  const filtered = libraries.filter((library) => library.type === libraryType);
  const selectData = filtered.map((library) => ({
    value: library.title,
    label: `${library.title} (${library.count} items)`,
  }));

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
          Failed to load libraries:{" "}
          {(error as Error)?.message || "Unknown error"}
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
          // Prevent deselection - if user clicks on already selected option, keep current value
          if (newValue !== null) {
            update(newValue);
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
