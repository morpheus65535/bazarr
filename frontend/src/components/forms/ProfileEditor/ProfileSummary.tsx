import { FunctionComponent } from "react";
import { Card, Divider, List, Stack, Text, Title } from "@mantine/core";
import {
  faBullseye,
  faListCheck,
  faSliders,
} from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { LanguageProfileSummary } from "@/utilities/languageProfileSummary";
import styles from "./ProfileEditor.module.scss";

export interface ProfileSummaryProps {
  summary: LanguageProfileSummary;
  /** Index of the requirement that stops searching, when one is selected. */
  highlightedRequirementIndex?: number | null;
}

const ProfileSummary: FunctionComponent<ProfileSummaryProps> = ({
  highlightedRequirementIndex = null,
  summary,
}) => {
  return (
    <Card withBorder padding="md" aria-label="What this means">
      <Stack gap="sm">
        <Title order={4}>What this means</Title>

        <Stack gap="xs">
          {summary.requirements.map((requirement, index) => {
            const isHighlighted = index === highlightedRequirementIndex;

            return (
              <div
                key={`${requirement.label}-${index}`}
                className={styles.summaryRequirement}
                data-cutoff={isHighlighted ? "true" : "false"}
              >
                <Text
                  size="xs"
                  c="dimmed"
                  tt="uppercase"
                  className={styles.summaryHeading}
                >
                  {isHighlighted && <FontAwesomeIcon icon={faBullseye} />}
                  {requirement.label}
                </Text>
                <Text size="sm">{requirement.text}</Text>
              </div>
            );
          })}
        </Stack>

        <Divider></Divider>

        <div>
          <Text
            size="xs"
            c="dimmed"
            tt="uppercase"
            className={styles.summaryHeading}
          >
            <FontAwesomeIcon icon={faBullseye} />
            Search completion
          </Text>
          <Text size="sm">{summary.completion}</Text>
        </div>

        {summary.restrictions.length > 0 && (
          <>
            <Divider></Divider>
            <div>
              <Text
                size="xs"
                c="dimmed"
                tt="uppercase"
                className={styles.summaryHeading}
              >
                <FontAwesomeIcon icon={faSliders} />
                Active restrictions
              </Text>
              <List size="sm" spacing={2}>
                {summary.restrictions.map((restriction) => (
                  <List.Item key={restriction}>{restriction}</List.Item>
                ))}
              </List>
            </div>
          </>
        )}

        {summary.caveats.length > 0 && (
          <Stack gap={4}>
            {summary.caveats.map((caveat) => (
              <Text key={caveat} size="xs" c="dimmed">
                {caveat}
              </Text>
            ))}
          </Stack>
        )}

        <Text size="xs" c="dimmed" className={styles.summaryHeading}>
          <FontAwesomeIcon icon={faListCheck} />
          {summary.requirements.length} requirement
          {summary.requirements.length === 1 ? "" : "s"}
        </Text>
      </Stack>
    </Card>
  );
};

export default ProfileSummary;
