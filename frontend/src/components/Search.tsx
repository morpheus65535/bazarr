import { FunctionComponent } from "react";
import { Kbd, TextInput } from "@mantine/core";
import { useOs } from "@mantine/hooks";
import { faSearch } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import Action from "@/components/inputs/Action";
import { spotlightApi } from "@/components/spotlight";
import styles from "./Search.module.scss";

const Search: FunctionComponent = () => {
  const os = useOs();

  const isMac = os === "macos";

  return (
    <>
      <Action
        hiddenFrom="sm"
        label="Search"
        icon={faSearch}
        size="sm"
        onClick={() => spotlightApi.open()}
      ></Action>
      <TextInput
        visibleFrom="sm"
        placeholder="Search"
        leftSection={<FontAwesomeIcon icon={faSearch} />}
        rightSection={
          <span className={styles.shortcut}>
            {isMac ? <Kbd>⌘</Kbd> : <Kbd>Ctrl</Kbd>}
            <span className={styles.separator}>+</span>
            <Kbd>K</Kbd>
          </span>
        }
        size="sm"
        readOnly
        onClick={() => spotlightApi.open()}
        classNames={{ input: styles.input }}
        rightSectionWidth={isMac ? 75 : 100}
      />
    </>
  );
};

export default Search;
