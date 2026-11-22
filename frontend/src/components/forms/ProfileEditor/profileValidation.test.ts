import { describe, expect, it } from "vitest";
import { ProfileDraft, toProfileDraft } from "./profileDraft";
import { validateProfileDraft } from "./profileValidation";

const item = (
  id: number,
  language: string,
  overrides: Partial<Language.ProfileItem> = {},
): Language.ProfileItem => ({
  id,
  language,
  audioExclude: "False",
  audioOnlyInclude: "False",
  hi: "False",
  forced: "False",
  ...overrides,
});

const draft = (overrides: Partial<ProfileDraft> = {}): ProfileDraft => ({
  profileId: 1,
  name: "Profile",
  tag: undefined,
  profileType: "enhanced",
  cutoff: null,
  mustContain: [],
  mustNotContain: [],
  originalFormat: false,
  groups: [{ id: 1, operator: "AND", items: [item(1, "en")] }],
  ...overrides,
});

const fieldsOf = (issues: ReturnType<typeof validateProfileDraft>) =>
  issues.map((issue) => issue.field);

describe("validateProfileDraft", () => {
  it("accepts a valid enhanced draft", () => {
    expect(validateProfileDraft(draft())).toEqual([]);
  });

  it("requires a name", () => {
    const issues = validateProfileDraft(draft({ name: "   " }));

    expect(fieldsOf(issues)).toContain("name");
  });

  it("rejects a tag with unsupported characters", () => {
    const issues = validateProfileDraft(draft({ tag: "Bad Tag!" }));

    expect(fieldsOf(issues)).toContain("tag");
  });

  it("requires at least one requirement", () => {
    const issues = validateProfileDraft(draft({ groups: [] }));

    expect(issues).toEqual([
      { field: "requirements", message: "Add at least one requirement." },
    ]);
  });

  it("requires every requirement to contain a language", () => {
    const issues = validateProfileDraft(
      draft({ groups: [{ id: 1, operator: "AND", items: [] }] }),
    );

    expect(issues).toContainEqual({
      field: "requirements",
      groupId: 1,
      message: "Add at least one language.",
    });
  });

  it("requires the user to choose a language for every row", () => {
    const issues = validateProfileDraft(
      draft({ groups: [{ id: 1, operator: "AND", items: [item(1, "")] }] }),
    );

    expect(issues).toContainEqual({
      field: "requirements",
      groupId: 1,
      itemId: 1,
      message: "Choose a language.",
    });
  });

  it("rejects a language repeated with the same subtitle type in one requirement", () => {
    const issues = validateProfileDraft(
      draft({
        groups: [
          { id: 1, operator: "AND", items: [item(1, "en"), item(2, "en")] },
        ],
      }),
    );

    expect(issues.some((issue) => /cannot repeat/.test(issue.message))).toBe(
      true,
    );
  });

  it("requires at least one language for a basic profile", () => {
    const basic = toProfileDraft({
      profileId: 2,
      name: "Basic",
      tag: undefined,
      items: [],
      cutoff: null,
      mustContain: [],
      mustNotContain: [],
      originalFormat: false,
    });

    expect(validateProfileDraft(basic)).toEqual([
      {
        field: "requirements",
        groupId: 1,
        message: "Add at least one language.",
      },
    ]);
  });
});
