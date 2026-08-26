import { FunctionComponent } from "react";
import { Outlet } from "react-router";
import { SegmentedTab, SegmentedTabs } from "@/pages/Settings/components";

const tabs: readonly SegmentedTab[] = [
  { value: "general", label: "Files & Search" },
  { value: "processing", label: "Processing" },
  { value: "translation", label: "Translation" },
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
