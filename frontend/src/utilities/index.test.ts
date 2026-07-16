import { describe, expect, it, vi } from "vitest";
import {
  BuildKey,
  filterSubtitleBy,
  fromPython,
  GetItemId,
  pathJoin,
  Reload,
  ScrollToTop,
  toggleState,
  toPython,
} from "@/utilities/index";

describe("fromPythonConversion", () => {
  it("should convert a true value", () => {
    expect(fromPython("True")).toBe(true);
  });

  it("should convert a false value", () => {
    expect(fromPython("False")).toBe(false);
  });

  it("should convert an undefined value", () => {
    expect(fromPython(undefined)).toBe(false);
  });
});

describe("toPythonConversion", () => {
  it("should convert a true value", () => {
    expect(toPython(true)).toBe("True");
  });

  it("should convert a false value", () => {
    expect(toPython(false)).toBe("False");
  });
});

describe("toggleState", () => {
  it("toggles the state and restores it after the wait", () => {
    vi.useFakeTimers();
    const dispatch = vi.fn();

    toggleState(dispatch, 100, false);

    expect(dispatch).toHaveBeenCalledWith(true);

    act(() => vi.advanceTimersByTime(100));

    expect(dispatch).toHaveBeenCalledWith(false);
    vi.useRealTimers();
  });
});

describe("GetItemId", () => {
  it("returns radarrId for a movie", () => {
    expect(GetItemId({ radarrId: 5 })).toBe(5);
  });

  it("returns sonarrEpisodeId for an episode", () => {
    expect(GetItemId({ sonarrEpisodeId: 10 })).toBe(10);
  });

  it("returns sonarrSeriesId for a series", () => {
    expect(GetItemId({ episodeFileCount: 1, sonarrSeriesId: 20 })).toBe(20);
  });

  it("returns undefined for an unknown item type", () => {
    expect(GetItemId({ foo: "bar" })).toBeUndefined();
  });
});

describe("BuildKey", () => {
  it("joins arguments with dashes", () => {
    expect(BuildKey("a", "b", 1)).toBe("a-b-1");
  });
});

describe("Reload", () => {
  it("reloads the window location", () => {
    const reload = vi.fn();
    Object.defineProperty(window, "location", {
      value: { ...window.location, reload },
      configurable: true,
    });

    Reload();

    expect(reload).toHaveBeenCalled();
  });
});

describe("ScrollToTop", () => {
  it("scrolls the window to the top", () => {
    const scrollTo = vi
      .spyOn(window, "scrollTo")
      .mockImplementation(() => undefined);

    ScrollToTop();

    expect(scrollTo).toHaveBeenCalledWith(0, 0);
    scrollTo.mockRestore();
  });
});

describe("pathJoin", () => {
  it("normalizes separators into a single slash", () => {
    expect(pathJoin("a", "b", "c")).toBe("a/b/c");
    expect(pathJoin("a/", "/b")).toBe("a/b");
    expect(pathJoin("a//b")).toBe("a/b");
  });
});

describe("filterSubtitleBy", () => {
  const subtitles = [
    { code2: "en", path: "/en.srt", name: "English", forced: false, hi: false },
    { code2: "fr", path: "/fr.srt", name: "French", forced: false, hi: false },
    { code2: "es", path: null, name: "Spanish", forced: false, hi: false },
  ] as Subtitle[];

  it("returns only subtitles with a path when no languages are requested", () => {
    expect(filterSubtitleBy(subtitles, [])).toEqual([
      subtitles[0],
      subtitles[1],
    ]);
  });

  it("filters by selected languages", () => {
    const languages = [{ code2: "en", name: "English" }] as Language.Info[];

    expect(filterSubtitleBy(subtitles, languages)).toEqual([
      subtitles[0],
      subtitles[1],
    ]);
  });
});

function act(fn: () => void) {
  fn();
}
