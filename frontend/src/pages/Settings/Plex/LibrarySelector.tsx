import { FunctionComponent } from "react";
import { Alert, Select, Stack, Text } from "@mantine/core";
import {
  usePlexAuthValidationQuery,
  usePlexLibrariesQuery,
} from "@/apis/hooks/plex";
import { Text as SettingsText } from "@/pages/Settings/components";
import { BaseInput, useBaseInput } from "@/pages/Settings/utilities/hooks";
import styles from "@/pages/Settings/Plex/LibrarySelector.module.scss";

export type LibrarySelectorProps = BaseInput<string> & {
  label: string;
  libraryType: "movie" | "show";
  placeholder?: string;
  description?: string;
  pathSettingKey?: string;
};

const LibrarySelector: FunctionComponent<LibrarySelectorProps> = (props) => {
  const {
    libraryType,
    placeholder,
    description,
    label,
    pathSettingKey,
    ...baseProps
  } = props;
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

  // Filter libraries by type and get selected library paths
  const filtered = libraries.filter((library) => library.type === libraryType);
  const selectedLibrary = filtered.find((library) => library.title === value);
  const selectedPaths = selectedLibrary?.locations || [];

  const selectData = filtered.map((library) => ({
    value: library.title,
    label: `${library.title} (${library.count} items)`,
  }));

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

  if (isLoading) {
    return (
      <Stack gap="xs" className={styles.librarySelector}>
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

  if (error) {
    return (
      <Stack gap="xs" className={styles.librarySelector}>
        <Alert color="red" variant="light" className={styles.alertMessage}>
          Failed to load libraries:{" "}
          {(error as Error)?.message || "Unknown error"}
        </Alert>
      </Stack>
    );
  }

  if (selectData.length === 0) {
    return (
      <Stack gap="xs" className={styles.librarySelector}>
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
          if (newValue !== null) {
            update(newValue);
          }
        }}
        allowDeselect={false}
        className={styles.selectField}
      />

      {pathSettingKey && selectedPaths.length > 0 && (
        <SettingsText
          label="Local Library Path"
          settingKey={pathSettingKey}
          settingOptions={{
            onLoaded: () => selectedPaths[0] || "",
          }}
          description="Local file system path where Bazarr can access your media files"
        />
      )}
    </div>
  );
};

export default LibrarySelector;
