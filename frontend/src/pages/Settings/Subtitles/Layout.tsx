import { FunctionComponent } from "react";
import { Outlet } from "react-router";
import { SegmentedTab, SegmentedTabs } from "@/pages/Settings/components";

const tabs: readonly SegmentedTab[] = [
  { value: "files", label: "Files" },
  { value: "search", label: "Search" },
  { value: "processing", label: "Processing" },
];

const SettingsSubtitlesLayout: FunctionComponent = () => {
  return (
    <>
      <SegmentedTabs basePath="/settings/subtitles" tabs={tabs}>
        <Outlet />
      </SegmentedTabs>
    </>
  );
};

export default SettingsSubtitlesLayout;
