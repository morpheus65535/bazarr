import { IconDefinition } from "@fortawesome/fontawesome-common-types";

type SidebarDefinition = LinkItemType | CollapseItemType;

type BaseSidebar = {
  icon: IconDefinition;
  name: string;
  hiddenKey?: string;
};

type LinkItemType = BaseSidebar & {
  link: string;
};

type CollapseItemType = BaseSidebar & {
  children: {
    name: string;
    link: string;
    hiddenKey?: string;
  }[];
};

type BadgeProvider = {
  [parent: string]: ChildBadgeProvider | number;
};

type ChildBadgeProvider = {
  [child: string]: number;
};
