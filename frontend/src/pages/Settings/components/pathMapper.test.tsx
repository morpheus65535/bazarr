import type { UseFormReturnType } from "@mantine/form";
import { render } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vitest } from "vitest";
import { FormContext, FormValues } from "@/pages/Settings/utilities/FormValues";
import { SettingsProvider } from "@/pages/Settings/utilities/SettingsProvider";
import { AllProviders } from "@/providers";
import { screen } from "@/tests";
import { PathMappingTable } from "./pathMapper";

const sonarrSettings = {
  general: {
    use_sonarr: true,
    path_mappings: [
      ["/from1", "/to1"],
      ["/from2", "/to2"],
    ],
  },
} as unknown as Settings;

const disabledSonarrSettings = {
  general: {
    use_sonarr: false,
    path_mappings: [],
  },
} as unknown as Settings;

function createForm(
  values: FormValues = { settings: {}, hooks: {} },
  setValues = vitest.fn(),
): UseFormReturnType<FormValues> {
  return { values, setValues } as unknown as UseFormReturnType<FormValues>;
}

function renderTable(
  type: "sonarr" | "radarr",
  settings: Settings,
  setValues = vitest.fn(),
) {
  const form = createForm({ settings: {}, hooks: {} }, setValues);

  return render(
    <AllProviders>
      <SettingsProvider value={settings}>
        <FormContext.Provider value={form}>
          <PathMappingTable type={type}></PathMappingTable>
        </FormContext.Provider>
      </SettingsProvider>
    </AllProviders>,
  );
}

describe("PathMappingTable", () => {
  it("renders a message when the feature is disabled", () => {
    renderTable("sonarr", disabledSonarrSettings);

    expect(
      screen.getByText(
        "Path Mappings will be available after staged changes are saved",
      ),
    ).toBeDefined();
  });

  it("renders the mappings when enabled", () => {
    renderTable("sonarr", sonarrSettings);

    expect(screen.getByDisplayValue("/from1")).toBeDefined();
    expect(screen.getByDisplayValue("/from2")).toBeDefined();
  });

  it("removes a mapping when the remove button is clicked", async () => {
    const setValues = vitest.fn();
    renderTable("sonarr", sonarrSettings, setValues);

    const removeButton = screen.getAllByRole("button", { name: "Remove" })[0];
    await userEvent.click(removeButton);

    expect(setValues).toHaveBeenCalled();
    const updater = setValues.mock.calls[0][0] as (
      values: FormValues,
    ) => FormValues;
    expect(updater({ settings: {}, hooks: {} })).toEqual({
      settings: {
        "settings-general-path_mappings": [["/from2", "/to2"]],
      },
      hooks: {},
    });
  });

  it("adds an empty mapping when the add button is clicked", async () => {
    const setValues = vitest.fn();
    renderTable("sonarr", sonarrSettings, setValues);

    const addButton = screen.getByRole("button", { name: "Add" });
    await userEvent.click(addButton);

    expect(setValues).toHaveBeenCalled();
    const updater = setValues.mock.calls[0][0] as (
      values: FormValues,
    ) => FormValues;
    expect(updater({ settings: {}, hooks: {} })).toEqual({
      settings: {
        "settings-general-path_mappings": [
          ["/from1", "/to1"],
          ["/from2", "/to2"],
          ["", ""],
        ],
      },
      hooks: {},
    });
  });
});
