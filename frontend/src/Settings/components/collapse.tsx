import React, {
  Dispatch,
  FunctionComponent,
  useContext,
  useMemo,
  useState,
} from "react";
import { Collapse } from "react-bootstrap";

type SupportType = string | boolean;

const CollapseContext = React.createContext<
  [SupportType, Dispatch<SupportType>]
>(["", (s) => {}]);
const CollapseUpdateContext = React.createContext<Dispatch<SupportType>>(
  (s) => {}
);

export function useCollapse() {
  return useContext(CollapseUpdateContext);
}

interface CollapseBoxType {
  Control: typeof CollapseBoxControl;
  Content: typeof CollapseBoxContent;
}

const CollapseBox: CollapseBoxType & FunctionComponent = ({ children }) => {
  const state = useState<boolean | string>(false);

  return (
    <CollapseContext.Provider value={state}>
      {children}
    </CollapseContext.Provider>
  );
};

const CollapseBoxControl: FunctionComponent = ({ children }) => {
  const context = useContext(CollapseContext);
  return (
    <CollapseUpdateContext.Provider value={context[1]}>
      {children}
    </CollapseUpdateContext.Provider>
  );
};

interface ContentProps {
  on?: (k: string) => boolean;
  eventKey?: string;
  indent?: boolean;
  children: JSX.Element | JSX.Element[];
}

const CollapseBoxContent: FunctionComponent<ContentProps> = ({
  on,
  eventKey,
  indent,
  children,
}) => {
  const [value] = useContext(CollapseContext);

  const open = useMemo(() => {
    if (on && typeof value === "string") {
      return on(value);
    } else if (eventKey) {
      return value === eventKey;
    } else {
      return value === true;
    }
  }, [on, value, eventKey]);

  return (
    <Collapse in={open} className={indent === false ? undefined : "ps-4"}>
      <div>{children}</div>
    </Collapse>
  );
};

CollapseBox.Control = CollapseBoxControl;
CollapseBox.Content = CollapseBoxContent;

export default CollapseBox;
