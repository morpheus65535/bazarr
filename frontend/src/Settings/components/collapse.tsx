import React, {
  Dispatch,
  FunctionComponent,
  useContext,
  useState,
  useEffect,
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

interface Props {}

const CollapseBox: CollapseBoxType & FunctionComponent<Props> = ({
  children,
}) => {
  const state = useState<boolean | string>("");

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
  eventKey?: string;
  on?: (k: string) => boolean;
  indent?: boolean;
  children: JSX.Element | JSX.Element[];
}

const CollapseBoxContent: FunctionComponent<ContentProps> = ({
  on,
  eventKey,
  indent,
  children,
}) => {
  const [open, setOpen] = useState(false);
  const [value] = useContext(CollapseContext);

  useEffect(() => {
    if (on && typeof value === "string") {
      setOpen(on(value));
    } else if (eventKey) {
      setOpen(value === eventKey);
    } else {
      setOpen(value === true);
    }
  }, [eventKey, value, on]);

  return (
    <Collapse in={open} className={indent === false ? undefined : "pl-4"}>
      <div>{children}</div>
    </Collapse>
  );
};

CollapseBox.Control = CollapseBoxControl;
CollapseBox.Content = CollapseBoxContent;

export default CollapseBox;
