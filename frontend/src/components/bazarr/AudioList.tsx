import { FunctionComponent } from "react";
import { Badge, BadgeProps, Group, GroupProps } from "@mantine/core";
import { BuildKey } from "@/utilities";

export type AudioListProps = GroupProps & {
  audios: Language.NullableCodeInfo[];
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
