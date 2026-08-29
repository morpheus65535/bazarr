import { FunctionComponent } from "react";
import { Outlet } from "react-router";
import { SegmentedTab, SegmentedTabs } from "@/pages/Settings/components";

const tabs: readonly SegmentedTab[] = [
  { value: "general", label: "General" },
  { value: "ui", label: "UI" },
  { value: "scheduler", label: "Scheduler" },
  { value: "maintenance", label: "Maintenance" },
];

const SettingsApplicationView: FunctionComponent = () => {
  return (
    <>
      <SegmentedTabs basePath="/settings/application" tabs={tabs}>
        <Outlet />
      </SegmentedTabs>
    </>
  );
};

export default SettingsApplicationView;
