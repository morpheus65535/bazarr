import { FunctionComponent } from "react";
import { Outlet } from "react-router";
import { useSystemSettings } from "@/apis/hooks";
import { SegmentedTab, SegmentedTabs } from "@/pages/Settings/components";

const SettingsIntegrationsView: FunctionComponent = () => {
  const { data: settings } = useSystemSettings();

  const tabs: readonly SegmentedTab[] = [
    {
      value: "plex",
      label: "Plex",
      status: settings?.general?.use_plex ? "success" : undefined,
    },
    {
      value: "jellyfin",
      label: "Jellyfin",
      status: settings?.general?.use_jellyfin ? "success" : undefined,
    },
  ];

  return (
    <>
      <SegmentedTabs basePath="/settings/integrations" tabs={tabs}>
        <Outlet />
      </SegmentedTabs>
    </>
  );
};

export default SettingsIntegrationsView;
