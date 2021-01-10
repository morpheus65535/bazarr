import React, { FunctionComponent, useMemo } from "react";

import { Selector } from "./Selector";

interface Props {
  className?: string;
  options: ExtendLanguage[];
  defaultSelect: ExtendLanguage[];
  onChange?: (lang: ExtendLanguage[]) => void;
}

const LanguageSelector: FunctionComponent<Props> = (props) => {
  const { className, options, defaultSelect, onChange } = props;

  const items = useMemo(() => {
    return options.flatMap<Pair>((lang) => {
      if (lang.code2 !== undefined) {
        return {
          key: lang.code2,
          value: lang.name,
        };
      } else {
        return [];
      }
    });
  }, [options]);

  const selection = useMemo(() => {
    return defaultSelect.flatMap((v) => {
      if (v.code2 !== undefined) {
        return v.code2;
      } else {
        return [];
      }
    });
  }, [defaultSelect]);

  return (
    <Selector
      className={className}
      multiply
      options={items}
      defaultKey={selection}
      onSelect={(k) => {
        const full = k.flatMap((v) => {
          const result = options.find((lang) => lang.code2 === v);
          if (result) {
            return result;
          } else {
            return [];
          }
        });
        onChange && onChange(full);
      }}
    ></Selector>
  );
};

export default LanguageSelector;
