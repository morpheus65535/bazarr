import { FunctionComponent, ReactNode, useState } from "react";
import { Link } from "react-router";
import { Box, Image, Text } from "@mantine/core";
import { faImage } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import styles from "./PosterCard.module.scss";

export interface PosterCardProps {
  title: string;
  year?: string;
  poster?: string | null;
  to: string;
  // Top-left corner, e.g. status icons
  header?: ReactNode;
  // Top-right corner, revealed on hover (always visible on touch devices)
  actions?: ReactNode;
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
  children,
}) => {
  const [loadFailed, setLoadFailed] = useState(false);

  const showPlaceholder = !poster || loadFailed;

  return (
    <Box className={styles.card}>
      <Link to={to} className={styles.link} aria-label={title}>
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
      </Link>
      {actions && <Box className={styles.actions}>{actions}</Box>}
    </Box>
  );
};

export default PosterCard;
