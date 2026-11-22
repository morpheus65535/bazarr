import { isLanguageRepeated } from "@/pages/Settings/Languages/profileModel";
import { ProfileDraft } from "./profileDraft";

export interface ProfileValidationIssue {
  field: "name" | "tag" | "requirements";
  groupId?: number;
  itemId?: number;
  message: string;
}

const tagPattern = /^[a-z_0-9-]+$/;

const validateItems = (
  items: readonly Language.ProfileItem[],
  duplicateMessage: string,
  groupId: number | undefined,
): ProfileValidationIssue[] => {
  const issues: ProfileValidationIssue[] = [];

  if (items.length === 0) {
    issues.push({
      field: "requirements",
      groupId,
      message: "Add at least one language.",
    });
    return issues;
  }

  for (const item of items) {
    if (item.language.length === 0) {
      issues.push({
        field: "requirements",
        groupId,
        itemId: item.id,
        message: "Choose a language.",
      });
    }
  }

  const selectedItems = items.filter((item) => item.language.length > 0);

  if (isLanguageRepeated(selectedItems)) {
    issues.push({ field: "requirements", groupId, message: duplicateMessage });
  }

  return issues;
};

export const validateProfileDraft = (
  draft: ProfileDraft,
): ProfileValidationIssue[] => {
  const issues: ProfileValidationIssue[] = [];

  if (draft.name.trim().length === 0) {
    issues.push({ field: "name", message: "Give this profile a name." });
  }

  if (draft.tag && !tagPattern.test(draft.tag)) {
    issues.push({
      field: "tag",
      message:
        "Tags allow lowercase letters, numbers, underscores and hyphens only.",
    });
  }

  if (draft.profileType === "enhanced") {
    if (draft.groups.length === 0) {
      issues.push({
        field: "requirements",
        message: "Add at least one requirement.",
      });
    }

    for (const group of draft.groups) {
      issues.push(
        ...validateItems(
          group.items,
          "A language cannot repeat with the same subtitle type in one requirement.",
          group.id,
        ),
      );
    }

    return issues;
  }

  const basicGroup = draft.groups[0];

  if (basicGroup === undefined) {
    issues.push({
      field: "requirements",
      message: "Add at least one language.",
    });
    return issues;
  }

  issues.push(
    ...validateItems(
      basicGroup.items,
      "A language cannot repeat with the same subtitle type.",
      basicGroup.id,
    ),
  );

  return issues;
};
