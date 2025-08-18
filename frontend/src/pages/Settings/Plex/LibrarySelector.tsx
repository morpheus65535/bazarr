import { FunctionComponent } from "react";
import { Alert, Select, Stack, Text } from "@mantine/core";
import {
  usePlexAuthValidationQuery,
  usePlexLibrariesQuery,
  usePlexSelectedServerQuery,
} from "@/apis/hooks/plex";
import { BaseInput, useBaseInput } from "@/pages/Settings/utilities/hooks";

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

  // Get selected server data to ensure libraries are fetched for the right server
  const { data: selectedServer } = usePlexSelectedServerQuery({
    enabled: isAuthenticated,
  });

  // Fetch libraries if authenticated and server is selected
  const {
    data: libraries = [],
    isLoading,
    error,
  } = usePlexLibrariesQuery({
    enabled: isAuthenticated && Boolean(selectedServer),
    serverId: selectedServer?.machineIdentifier,
  });

  // Filter libraries by type
  const filteredLibraries = libraries.filter((library) => {
    if (libraryType === "movie") {
      return library.type === "movie";
    }
    if (libraryType === "show") {
      return library.type === "show";
    }
    return false;
  });

  // If not authenticated, show message to use OAuth
  if (!isAuthenticated) {
    return (
      <Stack gap="xs">
        <Text fw={500}>{label}</Text>
        <Alert color="brand" variant="light">
          Enable Plex OAuth above to automatically discover your libraries.
        </Alert>
      </Stack>
    );
  }

  // If loading
  if (isLoading) {
    return (
      <Stack gap="xs">
        <Text fw={500}>{label}</Text>
        <Select
          {...rest}
          label={label}
          placeholder="Loading libraries..."
          data={[]}
          disabled
        />
      </Stack>
    );
  }

  // If error loading libraries
  if (error) {
    return (
      <Stack gap="xs">
        <Text fw={500}>{label}</Text>
        <Alert color="red" variant="light">
          Failed to load libraries: {error.message}
        </Alert>
      </Stack>
    );
  }

  // If no libraries found of this type
  if (filteredLibraries.length === 0) {
    return (
      <Stack gap="xs">
        <Text fw={500}>{label}</Text>
        <Alert color="gray" variant="light">
          No {libraryType} libraries found on your Plex server.
        </Alert>
      </Stack>
    );
  }

  // Prepare select data
  const selectData = filteredLibraries.map((library) => ({
    value: library.title,
    label: `${library.title} (${library.count} items)`,
  }));

  return (
    <Select
      {...rest}
      label={label}
      placeholder={placeholder || `Select ${libraryType} library...`}
      data={selectData}
      searchable
      clearable
      description={description}
      value={value || ""}
      onChange={(newValue) => update(newValue)}
    />
  );
};

export default LibrarySelector;
