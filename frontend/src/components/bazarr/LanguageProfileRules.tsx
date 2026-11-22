import { Fragment, FunctionComponent } from "react";
import { Badge, Group, Text } from "@mantine/core";
import { faBullseye } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { anyCutoff, itemLabel } from "@/components/forms/profileOptions";

const cutoffTitle = "Stops searching once this is found";

interface ItemBadgeProps {
  item: Language.ProfileItem;
  isCutoff: boolean;
}

const ItemBadge: FunctionComponent<ItemBadgeProps> = ({ isCutoff, item }) => (
  <Badge
    title={isCutoff ? cutoffTitle : undefined}
    color={isCutoff ? "brand" : "secondary"}
    leftSection={isCutoff ? <FontAwesomeIcon icon={faBullseye} /> : undefined}
  >
    {itemLabel(item)}
  </Badge>
);

interface GroupsProps {
  groups: Language.EnhancedGroup[];
  cutoff: number | null;
}

const relationshipLabel = (operator: Language.EnhancedGroup["operator"]) =>
  operator === "AND" ? "All of" : "Any of";

// Renders an enhanced profile as wrapping, readable groups. Additional groups are
// separate requirements, not a fallback chain.
const GroupsExpression: FunctionComponent<GroupsProps> = ({
  groups,
  cutoff,
}) => (
  <Group gap="xs" wrap="wrap" align="center">
    {groups.map((group, groupIndex) => {
      const isCutoff = group.id === cutoff || cutoff === anyCutoff;

      return (
        <Fragment key={group.id}>
          {groupIndex > 0 && (
            <Text span c="dimmed" size="sm">
              +
            </Text>
          )}
          <Group gap={4} wrap="wrap" align="center">
            <Text span size="xs" c="dimmed">
              {relationshipLabel(group.operator)}
            </Text>
            {group.items.map((item) => (
              <ItemBadge
                key={item.id}
                isCutoff={isCutoff}
                item={item}
              ></ItemBadge>
            ))}
          </Group>
        </Fragment>
      );
    })}
  </Group>
);

export type LanguageProfileRulesProfile = Pick<
  Language.Profile,
  "cutoff" | "items" | "profileType" | "groups"
>;

// Shows a languages profile's rules: the groups for enhanced profiles, and one
// badge per language for basic ones. The item that meets the cutoff is highlighted.
const LanguageProfileRules: FunctionComponent<{
  profile: LanguageProfileRulesProfile;
}> = ({ profile }) => {
  const { cutoff, groups, items, profileType } = profile;

  if (profileType === "enhanced" && groups) {
    return (
      <GroupsExpression groups={groups} cutoff={cutoff}></GroupsExpression>
    );
  }

  return (
    <Group gap="xs" wrap="wrap">
      {items.map((item) => (
        <ItemBadge
          key={item.id}
          isCutoff={item.id === cutoff || cutoff === anyCutoff}
          item={item}
        ></ItemBadge>
      ))}
    </Group>
  );
};

export default LanguageProfileRules;
