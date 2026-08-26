import { FunctionComponent } from "react";
import { Outlet } from "react-router";
import { SegmentedTab, SegmentedTabs } from "@/pages/Settings/components";

const tabs: readonly SegmentedTab[] = [
  { value: "general", label: "Selection" },
  { value: "mappings", label: "Mappings" },
  { value: "profiles", label: "Profiles" },
];

const SettingsLanguagesLayout: FunctionComponent = () => {
  return (
    <>
      <SegmentedTabs basePath="/settings/languages" tabs={tabs}>
        <Outlet />
      </SegmentedTabs>
    </>
  );
};

export default SettingsLanguagesLayout;
