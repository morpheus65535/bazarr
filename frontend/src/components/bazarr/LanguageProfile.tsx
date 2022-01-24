import { useLanguageProfiles } from "@/apis/hooks";
import React, { FunctionComponent, useMemo } from "react";

interface Props {
  index: number | null;
  className?: string;
  empty?: string;
}

const LanguageProfile: FunctionComponent<Props> = ({
  index,
  className,
  empty = "Unknown Profile",
}) => {
  const { data } = useLanguageProfiles();

  const name = useMemo(
    () => data?.find((v) => v.profileId === index)?.name ?? empty,
    [data, empty, index]
  );

  return <span className={className}>{name}</span>;
};

export default LanguageProfile;
