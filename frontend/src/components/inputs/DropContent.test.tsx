import { Dropzone } from "@mantine/dropzone";
import { describe, expect, it, vitest } from "vitest";
import { customRender, screen } from "@/tests";
import { DropContent } from "./DropContent";

describe("DropContent", () => {
  it("renders the upload subtitle instructions", () => {
    const onDrop = vitest.fn();
    customRender(
      <Dropzone onDrop={onDrop}>
        <DropContent />
      </Dropzone>,
    );

    expect(screen.getByText("Upload Subtitles")).toBeInTheDocument();
    expect(
      screen.getByText(
        "Attach as many files as you like, you will need to select file metadata before uploading",
      ),
    ).toBeInTheDocument();
  });
});
