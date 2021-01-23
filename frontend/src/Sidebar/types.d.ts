import { IconDefinition } from "@fortawesome/fontawesome-common-types";

interface SidebarDef {
  icon: IconDefinition;
  name: string;
  badge?: string;
  to?: string;
  children?: Child[];
}

interface Child {
  name: string;
  badge?: string;
  to: string;
}
