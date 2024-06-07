import { BuildKey } from "@/utilities";
import { Badge, BadgeProps, Group, GroupProps } from "@mantine/core";
import { FunctionComponent } from "react";

export type AudioListProps = GroupProps & {
  audios: Language.Info[];
  badgeProps?: BadgeProps;
};

const AudioList: FunctionComponent<AudioListProps> = ({
  audios,
  badgeProps,
  ...group
}) => {
  return (
    <Group gap="xs" {...group}>
      {audios.map((audio, idx) => (
        <Badge color="blue" key={BuildKey(idx, audio.code2)} {...badgeProps}>
          {audio.name}
        </Badge>
      ))}
    </Group>
  );
};

export default AudioList;
