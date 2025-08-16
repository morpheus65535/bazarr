import { Stack } from "@mantine/core";
import AuthSection from "./AuthSection";
import ServerSection from "./ServerSection";

export const PlexSettings = () => {
  return (
    <Stack gap="lg">
      <AuthSection />
      <ServerSection />
    </Stack>
  );
};

export default PlexSettings;
