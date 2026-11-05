import { FunctionComponent, ReactNode } from "react";
import { useLocation, useNavigate } from "react-router";
import { Group, Tabs, Text } from "@mantine/core";
import classes from "./SegmentedTabs.module.scss";

export interface SegmentedTab {
  value: string;
  label: string;
  /** Show a small status dot on the tab (e.g. "success" = configured/enabled). */
  status?: "success" | "warning" | "dimmed";
}

interface SegmentedTabsProps {
  basePath: string;
  tabs: readonly SegmentedTab[];
  children: ReactNode;
}

const findActiveTab = (
  pathname: string,
  tabs: readonly SegmentedTab[],
): string => {
  const normalizedPath = pathname.replace(/\/+$/, "");
  const match = tabs.find((t) => normalizedPath.endsWith(`/${t.value}`));
  return match?.value ?? tabs[0].value;
};

const statusLabels: Record<NonNullable<SegmentedTab["status"]>, string> = {
  success: "enabled",
  warning: "needs attention",
  dimmed: "inactive",
};

const SegmentedTabs: FunctionComponent<SegmentedTabsProps> = ({
  basePath,
  tabs,
  children,
}) => {
  const navigate = useNavigate();
  const location = useLocation();

  const activeTab = findActiveTab(location.pathname, tabs);

  return (
    <Tabs
      value={activeTab}
      onChange={(value) => value && navigate(`${basePath}/${value}`)}
      variant="none"
      classNames={{ list: classes.tabsList, tab: classes.tab }}
    >
      <Tabs.List>
        {tabs.map((tab) => (
          <Tabs.Tab
            key={tab.value}
            value={tab.value}
            aria-label={
              tab.status
                ? `${tab.label}, ${statusLabels[tab.status]}`
                : undefined
            }
          >
            <Group gap={6} wrap="nowrap" justify="center">
              {tab.status && (
                <Text
                  component="span"
                  c={tab.status}
                  fz={8}
                  lh={1}
                  data-testid={`tab-status-${tab.value}`}
                  aria-hidden="true"
                >
                  ●
                </Text>
              )}
              {tab.label}
            </Group>
          </Tabs.Tab>
        ))}
      </Tabs.List>
      <Tabs.Panel value={activeTab}>{children}</Tabs.Panel>
    </Tabs>
  );
};

export default SegmentedTabs;
