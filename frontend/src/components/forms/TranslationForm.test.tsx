import { describe, expect, it, vitest } from "vitest";
import { useSubtitleAction, useSystemSettings } from "@/apis/hooks";
import { useModals } from "@/modules/modals";
import { customRender, screen } from "@/tests";
import { useEnabledLanguages } from "@/utilities/languages";
import TranslationForm from "./TranslationForm";

vitest.mock("@/apis/hooks", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/apis/hooks")>();
  return {
    ...actual,
    useSubtitleAction: vitest.fn(),
    useSystemSettings: vitest.fn(),
  };
});

vitest.mock("@/utilities/languages", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/utilities/languages")>();
  return { ...actual, useEnabledLanguages: vitest.fn() };
});

vitest.mock("@/modules/modals", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/modules/modals")>();
  return { ...actual, useModals: vitest.fn() };
});

const mockUseSubtitleAction = vitest.mocked(useSubtitleAction);
const mockUseSystemSettings = vitest.mocked(useSystemSettings);
const mockUseEnabledLanguages = vitest.mocked(useEnabledLanguages);
const mockUseModals = vitest.mocked(useModals);

const selection = {
  id: 1,
  subtitlesId: 2,
  type: "episode",
  language: "en",
  path: "/subtitles/sub.srt",
  hi: "False",
  forced: "False",
} as FormType.ModifySubtitle;

const languages = [
  { code2: "en", name: "English" },
  { code2: "es", name: "Spanish" },
  { code2: "zz", name: "Zzz" },
] as Language.Info[];

const renderForm = (translatorType: string, geminiModel?: string) => {
  mockUseSystemSettings.mockReturnValue({
    data: {
      general: { theme: "dark" },
      translator: {
        translator_type: translatorType,
        gemini_model: geminiModel,
      },
    },
  } as unknown as ReturnType<typeof useSystemSettings>);
  mockUseEnabledLanguages.mockReturnValue({
    data: languages,
  } as unknown as ReturnType<typeof useEnabledLanguages>);
  mockUseSubtitleAction.mockReturnValue({
    mutateAsync: vitest.fn(),
    isPending: false,
  } as unknown as ReturnType<typeof useSubtitleAction>);
  mockUseModals.mockReturnValue({
    closeSelf: vitest.fn(),
  } as unknown as ReturnType<typeof useModals>);

  customRender(<TranslationForm selections={[selection]} />);
};

describe("TranslationForm", () => {
  it("renders the Google Translate service text", () => {
    renderForm("google_translate");

    expect(
      screen.getByText(/Google Translate will be used/),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/Enabled languages not listed here are unsupported/),
    ).toBeInTheDocument();
  });

  it("renders the Gemini service text with the model name", () => {
    renderForm("gemini", "gemini-pro");

    expect(screen.getByText(/Gemini \(gemini-pro\)/)).toBeInTheDocument();
  });

  it("renders the Lingarr service text", () => {
    renderForm("lingarr");

    expect(screen.getByText(/Lingarr/)).toBeInTheDocument();
  });
});
