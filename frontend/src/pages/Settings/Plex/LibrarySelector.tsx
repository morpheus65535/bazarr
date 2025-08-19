/* eslint-disable no-console */
import { FunctionComponent } from "react";
import { Alert, Select, Stack, Text } from "@mantine/core";
// Temporarily disabled for debugging
// import {
//   usePlexAuthValidationQuery,
//   usePlexLibrariesQuery,
// } from "@/apis/hooks/plex";
import { BaseInput, useBaseInput } from "@/pages/Settings/utilities/hooks";
import styles from "@/pages/Settings/Plex/LibrarySelector.module.scss";

export type LibrarySelectorProps = BaseInput<string> & {
  label: string;
  libraryType: "movie" | "show";
  placeholder?: string;
  description?: string;
};

// Simple render tracking without forbidden hooks
const renderCounts: { movie: number; show: number } = { movie: 0, show: 0 };
const lastProps: { movie: unknown; show: unknown } = {
  movie: null,
  show: null,
};

const LibrarySelector: FunctionComponent<LibrarySelectorProps> = (props) => {
  const { libraryType, placeholder, description, label, ...baseProps } = props;
  const { value, update, rest } = useBaseInput(baseProps);

  // Track render count and prop changes
  renderCounts[libraryType]++;
  const currentProps = { value, ...baseProps };
  const propsChanged =
    JSON.stringify(lastProps[libraryType]) !== JSON.stringify(currentProps);
  lastProps[libraryType] = currentProps;

  console.log(
    `[LibrarySelector-${libraryType}] RENDER #${renderCounts[libraryType]} - value: "${value}" settingKey: ${baseProps.settingKey} propsChanged: ${propsChanged}`,
  );
  console.log(
    `[LibrarySelector-${libraryType}] useBaseInput returns:`,
    "update function:",
    update.toString().slice(0, 80) + "...",
  );

  // Check if user is authenticated with OAuth - TEMPORARILY DISABLED FOR DEBUGGING
  // const { data: authData } = usePlexAuthValidationQuery();
  // const isAuthenticated = Boolean(
  //   authData?.valid && authData?.auth_method === "oauth",
  // );
  const isAuthenticated = false; // Hardcoded for debugging
  console.log(
    `[LibrarySelector-${libraryType}] Authentication check:`,
    isAuthenticated,
  );

  // Fetch libraries if authenticated - TEMPORARILY DISABLED FOR DEBUGGING
  // const {
  //   data: libraries = [],
  //   isLoading,
  //   error,
  // } = usePlexLibrariesQuery({
  //   enabled: isAuthenticated,
  // });
  const libraries: unknown[] = []; // Hardcoded for debugging
  const isLoading = false;
  const error = null;

  console.log(`[LibrarySelector-${libraryType}] Libraries query result:`, {
    librariesCount: libraries.length,
    isLoading,
    hasError: !!error,
    isAuthenticated,
  });

  // Filter libraries by type and prepare select data
  console.log(
    `[LibrarySelector-${libraryType}] Filtering libraries for type:`,
    libraryType,
  );
  const selectData: { value: string; label: string }[] = []; // Hardcoded empty for debugging
  console.log(
    `[LibrarySelector-${libraryType}] SelectData result:`,
    selectData,
  );

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
