import { Mock, vi, vitest } from "vitest";
import { useSettingsMutation, useSystemSettings } from "@/apis/hooks/system";
import { customRender, screen } from "@/tests";
import SettingsSchedulerView from "./index";

vi.mock("@/apis/hooks/system", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/apis/hooks/system")>();
  return {
    ...actual,
    useSystemSettings: vitest.fn(),
    useSettingsMutation: vitest.fn(),
  };
});

it("shows Sportarr sync and disk scan schedules when Sportarr is enabled", () => {
  (useSystemSettings as Mock).mockReturnValue({
    data: {
      general: { theme: "auto", instance_name: "Bazarr", use_sportarr: true },
      sportarr: {
        leagues_sync: 60,
        full_update: "Daily",
        full_update_day: 6,
        full_update_hour: 4,
      },
    } as unknown as Settings,
    isLoading: false,
    isRefetching: false,
  });
  (useSettingsMutation as Mock).mockReturnValue({
    mutate: vi.fn(),
    isPending: false,
  });

  customRender(<SettingsSchedulerView />);

  expect(
    screen.getByRole("combobox", { name: "Sync with Sportarr" }),
  ).toBeInTheDocument();
  expect(
    screen.getByRole("combobox", {
      name: "Update All Sports Subtitles from Disk",
    }),
  ).toBeInTheDocument();
});
