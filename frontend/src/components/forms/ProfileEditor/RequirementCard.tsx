import { FunctionComponent, useMemo } from "react";
import {
  Badge,
  Button,
  Card,
  Group,
  SegmentedControl,
  Stack,
  Text,
} from "@mantine/core";
import {
  faArrowDown,
  faArrowUp,
  faBullseye,
  faPlus,
  faTrash,
} from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { Action } from "@/components";
import { relationshipOptions } from "@/components/forms/profileOptions";
import { describeLanguageCondition } from "@/utilities/languageProfileSummary";
import LanguageRequirementRow, {
  LanguageOption,
} from "./LanguageRequirementRow";
import { ProfileValidationIssue } from "./profileValidation";
import styles from "./ProfileEditor.module.scss";

export interface RequirementCardProps {
  group: Language.EnhancedGroup;
  index: number;
  count: number;
  isCutoffGroup: boolean;
  languageData: readonly LanguageOption[];
  resolveLanguageName: (code: string) => string;
  issues: readonly ProfileValidationIssue[];
  onOperator: (operator: Language.EnhancedGroup["operator"]) => void;
  onMove: (direction: -1 | 1) => void;
  onRemoveGroup: () => void;
  onToggleCutoff: () => void;
  onAddItem: () => void;
  onUpdateItem: (itemId: number, patch: Partial<Language.ProfileItem>) => void;
  onRemoveItem: (itemId: number) => void;
}

const relationshipDescription = (
  operator: Language.EnhancedGroup["operator"],
): string =>
  operator === "AND"
    ? "Every language below must be found."
    : "Any single language below is enough.";

const RequirementCard: FunctionComponent<RequirementCardProps> = ({
  count,
  group,
  index,
  isCutoffGroup,
  issues,
  languageData,
  onAddItem,
  onMove,
  onOperator,
  onRemoveGroup,
  onRemoveItem,
  onToggleCutoff,
  onUpdateItem,
  resolveLanguageName,
}) => {
  const groupIssues = useMemo(
    () => issues.filter((issue) => issue.itemId === undefined),
    [issues],
  );

  const issuesByItemId = useMemo(() => {
    const map = new Map<number, string>();
    for (const issue of issues) {
      if (issue.itemId !== undefined) {
        map.set(issue.itemId, issue.message);
      }
    }
    return map;
  }, [issues]);

  const title = `Requirement ${index + 1}`;

  return (
    <Card
      withBorder
      padding="md"
      id={`profile-requirement-${group.id}`}
      tabIndex={-1}
      data-requirement-id={group.id}
      className={styles.requirement}
      data-operator={group.operator}
      data-cutoff={isCutoffGroup ? "true" : "false"}
      aria-label={title}
    >
      <Stack gap="sm">
        <Group
          justify="space-between"
          align="center"
          wrap="wrap"
          gap="xs"
          className={styles.requirementHeader}
        >
          <Group gap="xs" align="center" wrap="wrap">
            <span className={styles.numberBadge} aria-hidden>
              {index + 1}
            </span>
            <Text fw={600}>{title}</Text>
            {isCutoffGroup && (
              <Badge
                color="brand"
                variant="light"
                leftSection={<FontAwesomeIcon icon={faBullseye} />}
              >
                Stops searching
              </Badge>
            )}
          </Group>
          <Group gap={4}>
            <Action
              label={
                isCutoffGroup
                  ? "Stop searching after this requirement"
                  : "Stop searching when this requirement is satisfied"
              }
              icon={faBullseye}
              className={styles.touchAction}
              variant={isCutoffGroup ? "filled" : "subtle"}
              color={isCutoffGroup ? "brand" : "secondary"}
              onClick={onToggleCutoff}
            ></Action>
            <Action
              label={`Move ${title} up`}
              icon={faArrowUp}
              className={styles.touchAction}
              disabled={index === 0}
              onClick={() => onMove(-1)}
            ></Action>
            <Action
              label={`Move ${title} down`}
              icon={faArrowDown}
              className={styles.touchAction}
              disabled={index === count - 1}
              onClick={() => onMove(1)}
            ></Action>
            <Action
              label={`Remove ${title}`}
              icon={faTrash}
              c="danger"
              className={styles.touchAction}
              onClick={onRemoveGroup}
            ></Action>
          </Group>
        </Group>

        <Group gap="xs" align="center" wrap="wrap">
          <SegmentedControl
            size="sm"
            className={styles.relationship}
            aria-label={`${title} match rule`}
            data={relationshipOptions}
            value={group.operator}
            onChange={(value) =>
              onOperator(value as Language.EnhancedGroup["operator"])
            }
          ></SegmentedControl>
          <Text size="xs" c="dimmed">
            {relationshipDescription(group.operator)}
          </Text>
        </Group>

        <Stack gap="xs" className={styles.rows}>
          {group.items.map((item) => (
            <LanguageRequirementRow
              key={item.id}
              item={item}
              languageData={languageData}
              languageName={resolveLanguageName(item.language)}
              error={issuesByItemId.get(item.id)}
              condition={describeLanguageCondition(item, resolveLanguageName)}
              onChange={(patch) => onUpdateItem(item.id, patch)}
              onRemove={() => onRemoveItem(item.id)}
            ></LanguageRequirementRow>
          ))}
        </Stack>

        <Button
          id={`profile-add-language-${group.id}`}
          variant="default"
          size="xs"
          className={`${styles.addLanguage} ${styles.dashedButton}`}
          leftSection={<FontAwesomeIcon icon={faPlus} />}
          onClick={onAddItem}
        >
          Add language
        </Button>

        {groupIssues.map((issue) => (
          <Text key={issue.message} size="xs" c="var(--mantine-color-error)">
            {issue.message}
          </Text>
        ))}
      </Stack>
    </Card>
  );
};

export default RequirementCard;
