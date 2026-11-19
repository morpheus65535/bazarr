import userEvent from "@testing-library/user-event";
import { Mock, vi, vitest } from "vitest";
import {
  useSportsLeagueModification,
  useSportsLeagues,
  useSportsLeagueTags,
} from "@/apis/hooks/sports";
import { useSettingsMutation, useSystemSettings } from "@/apis/hooks/system";
import { customRender, screen } from "@/tests";
import SettingsSportarrView from "./index";

vi.mock("@/apis/hooks/system", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/apis/hooks/system")>();
  return {
    ...actual,
    useSystemSettings: vitest.fn(),
    useSettingsMutation: vitest.fn(),
  };
});

vi.mock("@/apis/hooks/sports", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/apis/hooks/sports")>();
  return {
    ...actual,
    useSportsLeagues: vitest.fn(),
    useSportsLeagueTags: vitest.fn(),
    useSportsLeagueModification: vitest.fn(),
  };
});

const mockedSettings = useSystemSettings as Mock;
const mockedSettingsMutation = useSettingsMutation as Mock;
const mockedLeagues = useSportsLeagues as Mock;
const mockedLeagueMutation = useSportsLeagueModification as Mock;
const mockedLeagueTags = useSportsLeagueTags as Mock;

describe("SettingsSportarrView", () => {
  beforeEach(() => {
    vitest.clearAllMocks();
    mockedSettings.mockReturnValue({
      data: {
        general: {
          theme: "auto",
          instance_name: "Bazarr",
          use_sportarr: true,
          minimum_score: 90,
          path_mappings_sports: [],
          league_default_enabled: true,
          league_default_profile: 7,
        },
        sportarr: {
          ip: "127.0.0.1",
          port: 1867,
          base_url: "/",
          apikey: "test-key",
          ssl: false,
          http_timeout: 60,
          excluded_tags: [],
          excluded_sports: [],
        },
      } as unknown as Settings,
      isLoading: false,
      isRefetching: false,
    });
    mockedSettingsMutation.mockReturnValue({
      mutate: vitest.fn(),
      isPending: false,
    });
    mockedLeagues.mockReturnValue({
      data: [
        { sportarrLeagueId: 1, profileId: null },
        { sportarrLeagueId: 2, profileId: 3 },
        { sportarrLeagueId: 3, profileId: null },
      ],
    });
    mockedLeagueTags.mockReturnValue({ data: ["No Subs", "UFC"] });
  });

  it("assigns the saved default profile only to unassigned leagues", async () => {
    const mutate = vitest.fn();
    mockedLeagueMutation.mockReturnValue({ mutate, isPending: false });

    customRender(<SettingsSportarrView />);

    await userEvent.click(
      screen.getByRole("button", {
        name: "Apply default profile to 2 unassigned leagues",
      }),
    );

    expect(mutate).toHaveBeenCalledWith({ id: [1, 3], profileId: [7, 7] });
  });

  it("keeps a Sportarr tag label when it is excluded", async () => {
    mockedLeagueMutation.mockReturnValue({
      mutate: vitest.fn(),
      isPending: false,
    });
    customRender(<SettingsSportarrView />);

    await userEvent.type(
      screen.getByRole("combobox", { name: "Excluded Tags" }),
      "No Subs{Enter}",
    );

    expect(screen.getByText("No Subs")).toBeInTheDocument();
  });
});
