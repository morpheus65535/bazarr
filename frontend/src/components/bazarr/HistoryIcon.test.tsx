import { describe, expect, it } from "vitest";
import { customRender, screen } from "@/tests";
import HistoryIcon from "./HistoryIcon";

describe("HistoryIcon", () => {
  it.each([
    [0, "Delete"],
    [1, "Download"],
    [2, "Manual"],
    [3, "Upgrade"],
    [4, "Upload"],
    [5, "Sync"],
    [6, "Translated"],
    [7, "Extracted"],
    [99, "Unknown"],
  ])("renders the expected icon for action %s", (action, label) => {
    customRender(<HistoryIcon action={action} />);

    expect(screen.getByLabelText(label)).toBeInTheDocument();
  });
});
