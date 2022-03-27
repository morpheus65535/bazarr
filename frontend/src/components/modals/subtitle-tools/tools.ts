import {
  faClock,
  faCode,
  faDeaf,
  faExchangeAlt,
  faFilm,
  faImage,
  faLanguage,
  faMagic,
  faPaintBrush,
  faPlay,
  faTextHeight,
} from "@fortawesome/free-solid-svg-icons";
import ColorTool from "./ColorTool";
import FrameRateTool from "./FrameRateTool";
import TimeTool from "./TimeTool";
import Translation from "./Translation";
import { ToolOptions } from "./types";

export const tools: ToolOptions[] = [
  {
    key: "sync",
    icon: faPlay,
    name: "Sync",
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
    name: "Add Color",
    modal: ColorTool,
  },
  {
    key: "change_frame_rate",
    icon: faFilm,
    name: "Change Frame Rate",
    modal: FrameRateTool,
  },
  {
    key: "adjust_time",
    icon: faClock,
    name: "Adjust Times",
    modal: TimeTool,
  },
  {
    key: "translation",
    icon: faLanguage,
    name: "Translate",
    modal: Translation,
  },
];
