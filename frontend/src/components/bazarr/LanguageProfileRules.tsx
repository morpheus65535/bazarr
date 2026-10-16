import { Fragment, FunctionComponent, useMemo } from "react";
import { Badge, Group, Text } from "@mantine/core";
import { faBullseye } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { anyCutoff } from "@/components/forms/profileOptions";

interface ItemBadgeProps {
  item: Language.ProfileItem;
  cutoff: boolean;
}

const ItemBadge: FunctionComponent<ItemBadgeProps> = ({ cutoff, item }) => {
  const text = useMemo(() => {
    const result =
      item.language +
      (item.hi === "True"
        ? ":HI"
        : item.forced === "True"
          ? ":Forced"
          : item.hi === "Excluded"
            ? ":Non-HI"
            : "");
    return result;
  }, [item.hi, item.forced, item.language]);
  return (
    <Badge
      title={cutoff ? "Ignore others if this one is available" : undefined}
      color={cutoff ? "brand" : "secondary"}
      leftSection={cutoff ? <FontAwesomeIcon icon={faBullseye} /> : undefined}
    >
      {text}
    </Badge>
  );
};

interface GroupsProps {
  groups: Language.EnhancedGroup[];
  cutoff: number | null;
}

// Renders an enhanced profile as an expression, for example (en AND fr) > de. The cutoff group is highlighted.
const GroupsExpression: FunctionComponent<GroupsProps> = ({
  groups,
  cutoff,
}) => {
  return (
    <Group gap="xs" wrap="nowrap">
      {groups.map((group, groupIndex) => {
        const isCutoff = group.id === cutoff || cutoff === anyCutoff;
        const parenthesized = group.items.length > 1;

        return (
          <Fragment key={group.id}>
            {groupIndex > 0 && (
              <Text span c="dimmed">
                &gt;
              </Text>
            )}
            {parenthesized && (
              <Text span c="dimmed">
                (
              </Text>
            )}
            {group.items.map((item, itemIndex) => (
              <Fragment key={item.id}>
                {itemIndex > 0 && (
                  <Text span size="sm" c="dimmed">
                    {group.operator}
                  </Text>
                )}
                <ItemBadge cutoff={isCutoff} item={item}></ItemBadge>
              </Fragment>
            ))}
            {parenthesized && (
              <Text span c="dimmed">
                )
              </Text>
            )}
          </Fragment>
        );
      })}
    </Group>
  );
};

export type LanguageProfileRulesProfile = Pick<
  Language.Profile,
  "cutoff" | "items" | "profileType" | "groups"
>;

// Shows a languages profile's rules: the expression for enhanced profiles, and one badge per language for basic
// ones. The item that meets the cutoff is highlighted in both cases.
const LanguageProfileRules: FunctionComponent<{
  profile: LanguageProfileRulesProfile;
}> = ({ profile }) => {
  const { items, cutoff, profileType, groups } = profile;

  if (profileType === "enhanced" && groups) {
    return <GroupsExpression groups={groups} cutoff={cutoff} />;
  }

  return (
    <Group gap="xs" wrap="nowrap">
      {items.map((v, i) => {
        const isCutoff = v.id === cutoff || cutoff === anyCutoff;
        return <ItemBadge key={i} cutoff={isCutoff} item={v}></ItemBadge>;
      })}
    </Group>
  );
};

export default LanguageProfileRules;
