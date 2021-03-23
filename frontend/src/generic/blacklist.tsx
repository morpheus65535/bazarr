import { faFileExcel } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import React, { FunctionComponent } from "react";
import { AsyncButton } from "../components";

interface Props {
  history: History.Base;
  update: () => void;
  promise: (form: FormType.AddBlacklist) => Promise<void>;
}

export const BlacklistButton: FunctionComponent<Props> = ({
  history,
  update,
  promise,
}) => {
  const { provider, subs_id, language, subtitles_path, blacklisted } = history;

  if (subs_id && provider && language) {
    return (
      <AsyncButton
        size="sm"
        variant="light"
        noReset
        disabled={blacklisted}
        promise={() => {
          const { code2 } = language;
          const form: FormType.AddBlacklist = {
            provider,
            subs_id,
            subtitles_path,
            language: code2,
          };
          return promise(form);
        }}
        onSuccess={update}
      >
        <FontAwesomeIcon icon={faFileExcel}></FontAwesomeIcon>
      </AsyncButton>
    );
  } else {
    return null;
  }
};
