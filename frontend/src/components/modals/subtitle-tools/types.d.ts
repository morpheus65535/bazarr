import { ModalComponent } from "@/modules/modals/WithModal";
import { IconDefinition } from "@fortawesome/free-solid-svg-icons";

export interface ToolOptions {
  key: string;
  icon: IconDefinition;
  name: string;
  modal?: ModalComponent;
}
