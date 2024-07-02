import { FunctionComponent, useMemo } from "react";
import { useLanguageProfiles } from "@/apis/hooks";

interface Props {
  index: number | null;
  empty?: string;
}

const LanguageProfileName: FunctionComponent<Props> = ({
  index,
  empty = "Unknown Profile",
}) => {
  const { data } = useLanguageProfiles();

  const name = useMemo(
    () => data?.find((v) => v.profileId === index)?.name ?? empty,
    [data, empty, index],
  );

  return <>{name}</>;
};

export default LanguageProfileName;
