import Language from "@/components/bazarr/Language";
import { Badge } from "@mantine/core";
import { FunctionComponent } from "react";

interface Props {
  seriesId: number;
  episodeId: number;
  missing?: boolean;
  subtitle: Subtitle;
}

export const Subtitle: FunctionComponent<Props> = ({
  seriesId,
  episodeId,
  missing,
  subtitle,
}) => {
  return (
    <Badge color={missing ? "yellow" : undefined}>
      <Language.Text value={subtitle} long={false}></Language.Text>
    </Badge>
  );
};
