import { createRef } from "react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vitest } from "vitest";
import { SportsEventHistoryModal } from "@/components/modals";
import { AppTable as TableInstance } from "@/components/tables/features";
import { useModals } from "@/modules/modals";
import { customRender, screen } from "@/tests";
import Table from "./table";

vitest.mock("@/modules/modals", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/modules/modals")>();
  return { ...actual, useModals: vitest.fn() };
});

const mockUseModals = vitest.mocked(useModals);

const createEvent = (
  overrides: Partial<Item.SportsEvent> = {},
): Item.SportsEvent =>
  ({
    sportsEventId: 12,
    sportarrLeagueId: 4,
    title: "UFC 300",
    partName: null,
    partNumber: 0,
    season: 2024,
    episode: 1,
    monitored: true,
    path: "/sports/ufc/ufc-300.mkv",
    sceneName: "UFC.300",
    broadcastDate: "2024-04-13",
    audioLanguage: [],
    subtitles: [],
    missingSubtitles: [],
    ...overrides,
  }) as Item.SportsEvent;

const mountTable = (event: Item.SportsEvent) => {
  const openContextModal = vitest.fn();
  mockUseModals.mockReturnValue({
    openContextModal,
  } as unknown as ReturnType<typeof useModals>);

  customRender(
    <Table
      ref={createRef<TableInstance<Item.SportsEvent>>()}
      events={[event]}
      onAllRowsExpandedChanged={vitest.fn()}
    />,
  );

  return openContextModal;
};

describe("SportsEvents table", () => {
  it("names the part in the history modal title", async () => {
    const event = createEvent({ partName: "Main Card" });
    const openContextModal = mountTable(event);

    await userEvent.click(screen.getByRole("button", { name: "History" }));

    expect(openContextModal).toHaveBeenCalledWith(
      SportsEventHistoryModal,
      { event },
      { title: "History - UFC 300 - Main Card" },
    );
  });

  it("uses the event title alone for a single file event", async () => {
    const event = createEvent();
    const openContextModal = mountTable(event);

    await userEvent.click(screen.getByRole("button", { name: "History" }));

    expect(openContextModal).toHaveBeenCalledWith(
      SportsEventHistoryModal,
      { event },
      { title: "History - UFC 300" },
    );
  });
});
