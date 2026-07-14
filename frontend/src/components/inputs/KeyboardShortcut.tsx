import { FunctionComponent } from "react";
import { Kbd, KbdProps } from "@mantine/core";
import { useOs } from "@mantine/hooks";

interface KeyboardShortcutProps {
  keys: string[];
  size?: KbdProps["size"];
}

const KeyboardShortcut: FunctionComponent<KeyboardShortcutProps> = ({
  keys,
  size = "xs",
}) => {
  const os = useOs();
  const isMac = os === "macos";

  const resolved = keys.map((key) =>
    key === "mod" ? (isMac ? "⌘" : "Ctrl") : key,
  );

  return (
    <span style={{ display: "inline-flex", gap: 2, alignItems: "center" }}>
      {resolved.map((key, idx) => (
        <Kbd key={idx} size={size}>
          {key}
        </Kbd>
      ))}
    </span>
  );
};

export default KeyboardShortcut;
