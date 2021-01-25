import React, { FunctionComponent, useMemo } from "react";

import { Selector } from "./Selector";

interface RootProps {
  disabled?: boolean;
  className?: string;
  variant?: string;
  options: Language[];
}

interface SingleProps extends RootProps {
  multiple?: false;
  defaultSelect?: Language;
  onChange?: (lang: Language) => void;
}

interface MultiProps extends RootProps {
  multiple: true;
  defaultSelect?: Language[];
  onChange?: (lang: Language[]) => void;
}

type Props = MultiProps | SingleProps;

const LanguageSelector: FunctionComponent<Props> = (props) => {
  const { disabled, className, variant, options, ...other } = props;
  const selector = { disabled, className, variant };

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

    if (other.multiple) {
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

  if (other.multiple) {
    return (
      <Selector
        {...selector}
        multiple
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
        {...selector}
        multiple={false}
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
