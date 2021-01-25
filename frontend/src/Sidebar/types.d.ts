import { IconDefinition } from "@fortawesome/fontawesome-common-types";

type SidebarDefinition = LinkItemType | CollapseItemType;

type LinkItemType = {
  icon: IconDefinition;
  name: string;
  link: string;
};

type CollapseItemType = {
  icon: IconDefinition;
  name: string;
  children: {
    name: string;
    link: string;
  }[];
};

type BadgeProvider = {
  [parent: string]: ChildBadgeProvider | number;
};

type ChildBadgeProvider = {
  [child: string]: number;
};
