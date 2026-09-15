import { describe, expect, it } from "vitest";
import { customRender, screen } from "@/tests";
import AudioList from "./AudioList";

const english = { code2: "en", name: "English" } as Language.Info;
const chinese = { code2: "zh", name: "Chinese Simplified" } as Language.Info;

describe("AudioList", () => {
  it("renders audio language badges with normalized names", () => {
    customRender(<AudioList audios={[english, chinese]} />);

    expect(screen.getByText("English")).toBeInTheDocument();
    expect(screen.getByText("Chinese")).toBeInTheDocument();
  });

  it("renders no badges when audios is empty", () => {
    customRender(<AudioList audios={[]} />);

    expect(screen.queryByText("English")).not.toBeInTheDocument();
  });
});
