import { FunctionComponent } from "react";
import { Outlet } from "react-router";
import { useSystemSettings } from "@/apis/hooks";
import { SegmentedTab, SegmentedTabs } from "@/pages/Settings/components";

const SettingsLibraryView: FunctionComponent = () => {
  const { data: settings } = useSystemSettings();

  const tabs: readonly SegmentedTab[] = [
    {
      value: "sonarr",
      label: "Sonarr",
      status: settings?.general?.use_sonarr ? "success" : undefined,
    },
    {
      value: "radarr",
      label: "Radarr",
      status: settings?.general?.use_radarr ? "success" : undefined,
    },
  ];

  return (
    <>
      <SegmentedTabs basePath="/settings/library" tabs={tabs}>
        <Outlet />
      </SegmentedTabs>
    </>
  );
};

export default SettingsLibraryView;
