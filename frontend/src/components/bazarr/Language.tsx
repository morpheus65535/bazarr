import React, { FunctionComponent, useMemo } from "react";

interface Props {
  value: Language.Info;
  className?: string;
  long?: boolean;
}

const Language: FunctionComponent<Props> = ({ value, className, long }) => {
  const result = useMemo(() => {
    let lang = value.code2;
    let hi = ":HI";
    let forced = ":Forced";
    if (long) {
      lang = value.name;
      hi = " HI";
      forced = " Forced";
    }

    let res = lang;
    if (value.hi) {
      res += hi;
    } else if (value.forced) {
      res += forced;
    }
    return res;
  }, [value, long]);

  return (
    <span title={value.name} className={className}>
      {result}
    </span>
  );
};

export default Language;
