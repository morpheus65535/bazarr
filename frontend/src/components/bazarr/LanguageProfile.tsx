import { useLanguageProfiles } from "@/apis/hooks";
import React, { FunctionComponent, useMemo } from "react";

interface Props {
  index: number | null;
  className?: string;
}

const LanguageProfile: FunctionComponent<Props> = ({ index, className }) => {
  const { data } = useLanguageProfiles();

  const name = useMemo(
    () => data?.find((v) => v.profileId === index)?.name ?? "Unknown Profile",
    [data, index]
  );

  return <span className={className}>{name}</span>;
};

export default LanguageProfile;
