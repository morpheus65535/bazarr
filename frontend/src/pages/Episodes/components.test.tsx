import { describe, expect, it, vitest } from "vitest";
import {
  useEpisodeSubtitleModification,
  useSubtitleAction,
} from "@/apis/hooks";
import { useModals } from "@/modules/modals";
import { customRender, screen } from "@/tests";
import { Subtitle } from "./components";

vitest.mock("@/apis/hooks", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/apis/hooks")>();
  return {
    ...actual,
    useSubtitleAction: vitest.fn(),
    useEpisodeSubtitleModification: vitest.fn(),
  };
});

vitest.mock("@/modules/modals", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/modules/modals")>();
  return { ...actual, useModals: vitest.fn() };
});

const mockUseSubtitleAction = vitest.mocked(useSubtitleAction);
const mockUseEpisodeSubtitleModification = vitest.mocked(
  useEpisodeSubtitleModification,
);
const mockUseModals = vitest.mocked(useModals);

const externalSubtitle = {
  code2: "en",
  name: "English",
  hi: false,
  forced: false,
  path: "/subtitles/sub.srt",
  embeddedTrackId: null,
  fileSize: 0,
  id: 1,
} as Subtitle;

const embeddedSubtitle = {
  code2: "en",
  name: "English",
  hi: false,
  forced: false,
  path: null,
  embeddedTrackId: 1,
  fileSize: 0,
  id: 2,
} as Subtitle;

function renderSubtitle(
  props?: Partial<React.ComponentProps<typeof Subtitle>>,
) {
  mockUseSubtitleAction.mockReturnValue({
    mutateAsync: vitest.fn(),
  } as unknown as ReturnType<typeof useSubtitleAction>);
  mockUseEpisodeSubtitleModification.mockReturnValue({
    download: { mutateAsync: vitest.fn() },
    remove: { mutateAsync: vitest.fn() },
  } as unknown as ReturnType<typeof useEpisodeSubtitleModification>);
  mockUseModals.mockReturnValue({
    openContextModal: vitest.fn(),
    openConfirmModal: vitest.fn(),
    closeSelf: vitest.fn(),
    closeModal: vitest.fn(),
    openModal: vitest.fn(),
    closeAll: vitest.fn(),
  } as unknown as ReturnType<typeof useModals>);

  customRender(
    <Subtitle
      seriesId={1}
      episodeId={2}
      mediaTitle="Episode Title"
      subtitle={externalSubtitle}
      {...props}
    />,
  );
}

describe("Subtitle", () => {
  it("renders an external subtitle", () => {
    renderSubtitle();
    expect(screen.getByText("en")).toBeInTheDocument();
  });

  it("renders an embedded subtitle", () => {
    renderSubtitle({ subtitle: embeddedSubtitle });
    expect(screen.getByText("en")).toBeInTheDocument();
  });

  it("renders a missing subtitle", () => {
    renderSubtitle({ missing: true, subtitle: embeddedSubtitle });
    expect(screen.getByText("en")).toBeInTheDocument();
  });
});
