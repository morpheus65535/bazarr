import React, { FunctionComponent, useMemo } from "react";

import { Selector } from "./Selector";

interface RootProps {
  className?: string;
  options: ExtendLanguage[];
}

interface SingleProps extends RootProps {
  multiply?: false;
  defaultSelect?: ExtendLanguage;
  onChange?: (lang: ExtendLanguage) => void;
}

interface MultiProps extends RootProps {
  multiply: true;
  defaultSelect?: ExtendLanguage[];
  onChange?: (lang: ExtendLanguage[]) => void;
}

type Props = MultiProps | SingleProps;

const LanguageSelector: FunctionComponent<Props> = (props) => {
  const { className, options, ...other } = props;

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

  const selection: string[] = useMemo(() => {
    if (other.defaultSelect === undefined) {
      return [];
    }

    if (other.multiply) {
      return other.defaultSelect.flatMap((v) => {
        if (v.code2 !== undefined) {
          return v.code2 ?? "";
        } else {
          return [];
        }
      });
    } else {
      return [other.defaultSelect.code2 ?? ""];
    }
  }, [other]);

  if (other.multiply) {
    return (
      <Selector
        className={className}
        multiply={true}
        options={items}
        defaultKey={selection}
        onMultiSelect={(k) => {
          const full = k.flatMap((v) => {
            const result = options.find((lang) => lang.code2 === v);
            if (result) {
              return result;
            } else {
              return [];
            }
          });
          other.onChange && other.onChange(full);
        }}
      ></Selector>
    );
  } else {
    const defaultKey = selection.length > 0 ? selection[0] : undefined;
    return (
      <Selector
        className={className}
        multiply={false}
        options={items}
        defaultKey={defaultKey}
        onSelect={(k) => {
          const result = options.find((lang) => lang.code2 === k);
          if (result) {
            other.onChange && other.onChange(result);
          }
        }}
      ></Selector>
    );
  }
};

export default LanguageSelector;
