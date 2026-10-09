// @vitest-environment node
import { assToHtml, toRenderable } from "./subtitles";

describe("assToHtml", () => {
  it("should translate formatting toggles to HTML tags", () => {
    expect(assToHtml("{\\i1}Italic{\\i0} {\\b1}Bold{\\b0}")).toBe(
      "<i>Italic</i> <b>Bold</b>",
    );
  });

  it("should translate combined toggles in a single block", () => {
    expect(assToHtml("{\\i1\\b1}both{\\i0\\b0}")).toBe("<i><b>both</i></b>");
  });

  it("should drop positioning and other override tags", () => {
    expect(assToHtml("{\\an8}top {\\pos(400,570)}positioned")).toBe(
      "top positioned",
    );
  });

  it("should convert line breaks and hard spaces", () => {
    expect(assToHtml("Two\\Nlines\\hjoined")).toBe("Two\nlines joined");
  });

  it("should escape HTML in the content", () => {
    expect(assToHtml("<script> & {\\i1}text{\\i0}")).toBe(
      "&lt;script&gt; &amp; <i>text</i>",
    );
  });
});

describe("toRenderable", () => {
  it("should translate content containing ASS markup", () => {
    expect(toRenderable("{\\i1}olá{\\i0}")).toBe("<i>olá</i>");
  });

  it("should keep SRT content untouched", () => {
    expect(toRenderable("plain <i>srt line</i>")).toBe("plain <i>srt line</i>");
  });
});
