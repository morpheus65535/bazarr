import { FunctionComponent } from "react";
import { Outlet } from "react-router";
import { SegmentedTab, SegmentedTabs } from "@/pages/Settings/components";

const tabs: readonly SegmentedTab[] = [
  { value: "subtitles", label: "Subtitles" },
  { value: "translation", label: "Translation" },
  { value: "protection", label: "Protection" },
  { value: "metadata", label: "Metadata" },
  { value: "advanced", label: "Advanced" },
];

const SettingsProvidersLayout: FunctionComponent = () => {
  return (
    <>
      <SegmentedTabs basePath="/settings/providers" tabs={tabs}>
        <Outlet />
      </SegmentedTabs>
    </>
  );
};

export default SettingsProvidersLayout;
