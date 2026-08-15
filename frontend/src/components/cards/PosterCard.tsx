import { FunctionComponent, ReactNode, useState } from "react";
import { Link } from "react-router";
import { Box, Checkbox, Image, Text, UnstyledButton } from "@mantine/core";
import { faImage } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import clsx from "clsx";
import styles from "./PosterCard.module.scss";

export interface PosterCardSelection {
  checked: boolean;
  onChange: () => void;
  pending?: boolean;
}

export interface PosterCardProps {
  title: string;
  year?: string;
  poster?: string | null;
  to: string;
  // Top-left corner, e.g. status icons
  header?: ReactNode;
  // Top-right corner, revealed on hover (always visible on touch devices)
  actions?: ReactNode;
  selection?: PosterCardSelection;
  // Bottom overlay content rendered below the title, e.g. progress or badges
  children?: ReactNode;
}

const PosterCard: FunctionComponent<PosterCardProps> = ({
  title,
  year,
  poster,
  to,
  header,
  actions,
  selection,
  children,
}) => {
  const [loadFailed, setLoadFailed] = useState(false);

  const showPlaceholder = !poster || loadFailed;

  const content = (
    <>
      {showPlaceholder ? (
        <Box className={styles.placeholder}>
          <FontAwesomeIcon icon={faImage} size="2x"></FontAwesomeIcon>
        </Box>
      ) : (
        <Image
          src={poster}
          alt={title}
          fit="cover"
          loading="lazy"
          onError={() => setLoadFailed(true)}
        ></Image>
      )}
      {header && <Box className={styles.header}>{header}</Box>}
      <Box className={styles.overlay}>
        <Text className={styles.title} lineClamp={2}>
          {title}
        </Text>
        {year && <Text className={styles.year}>{year}</Text>}
        {children}
      </Box>
    </>
  );

  return (
    <Box
      className={clsx(
        styles.card,
        selection?.checked && styles.selected,
        selection?.pending && styles.pending,
      )}
    >
      {selection ? (
        <UnstyledButton
          aria-pressed={selection.checked}
          aria-label={`Select ${title}`}
          className={styles.link}
          onClick={selection.onChange}
        >
          {content}
        </UnstyledButton>
      ) : (
        <Link to={to} className={styles.link} aria-label={title}>
          {content}
        </Link>
      )}
      {selection ? (
        <Box className={styles.selection}>
          <Checkbox
            aria-hidden
            tabIndex={-1}
            readOnly
            checked={selection.checked}
            style={{ pointerEvents: "none" }}
          ></Checkbox>
        </Box>
      ) : (
        actions && <Box className={styles.actions}>{actions}</Box>
      )}
    </Box>
  );
};

export default PosterCard;
