import { useMemo } from "react";
import {
  faAlignJustify,
  faClock,
  faCode,
  faDeaf,
  faExchangeAlt,
  faEye,
  faFaceGrinStars,
  faFilm,
  faImage,
  faLanguage,
  faMagic,
  faPaintBrush,
  faPlay,
  faTextHeight,
  IconDefinition,
} from "@fortawesome/free-solid-svg-icons";
import { ColorToolModal } from "@/components/forms/ColorToolForm";
import { FrameRateModal } from "@/components/forms/FrameRateForm";
import { SubtitlePreviewModal } from "@/components/forms/SubtitlePreview";
import { SyncSubtitleModal } from "@/components/forms/SyncSubtitleForm";
import { TimeOffsetModal } from "@/components/forms/TimeOffsetForm";
import { TranslationModal } from "@/components/forms/TranslationForm";
import { TwoPointFitModal } from "@/components/forms/TwoPointFit";
import { ModalComponent } from "@/modules/modals/WithModal";

export interface ToolOptions {
  key: string;
  icon: IconDefinition;
  name: string;
  modal?: ModalComponent<{
    selections: FormType.ModifySubtitle[];
  }>;
}

export const useTools = () =>
  useMemo<ToolOptions[]>(
    () => [
      {
        key: "preview",
        icon: faEye,
        name: "Preview...",
        modal: SubtitlePreviewModal,
      },
      {
        key: "sync",
        icon: faPlay,
        name: "Sync...",
        modal: SyncSubtitleModal,
      },
      {
        key: "remove_HI",
        icon: faDeaf,
        name: "Remove HI Tags",
      },
      {
        key: "remove_tags",
        icon: faCode,
        name: "Remove Style Tags",
      },
      {
        key: "emoji",
        icon: faFaceGrinStars,
        name: "Remove Emoji",
      },
      {
        key: "OCR_fixes",
        icon: faImage,
        name: "OCR Fixes",
      },
      {
        key: "common",
        icon: faMagic,
        name: "Common Fixes",
      },
      {
        key: "fix_uppercase",
        icon: faTextHeight,
        name: "Fix Uppercase",
      },
      {
        key: "reverse_rtl",
        icon: faExchangeAlt,
        name: "Reverse RTL",
      },
      {
        key: "add_color",
        icon: faPaintBrush,
        name: "Add Color...",
        modal: ColorToolModal,
      },
      {
        key: "change_frame_rate",
        icon: faFilm,
        name: "Change Frame Rate...",
        modal: FrameRateModal,
      },
      {
        key: "adjust_time",
        icon: faClock,
        name: "Adjust Times...",
        modal: TimeOffsetModal,
      },
      {
        key: "two_point_fit",
        icon: faAlignJustify,
        name: "Two-Point Fit...",
        modal: TwoPointFitModal,
      },
      {
        key: "translation",
        icon: faLanguage,
        name: "Translate...",
        modal: TranslationModal,
      },
    ],
    [],
  );
