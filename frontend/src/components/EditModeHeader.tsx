import { faCheck, faList, faUndo } from "@fortawesome/free-solid-svg-icons";
import React, { FunctionComponent, useCallback, useMemo } from "react";
import { connect } from "react-redux";
import { ContentHeader } from ".";
import { Selector } from "./inputs";

interface Props {
  profiles: LanguagesProfile[];
  editState: [boolean, React.Dispatch<boolean>];
}

function mapStateToProps({ system }: StoreState) {
  return {
    profiles: system.languagesProfiles.items,
  };
}

const EditModeHeader: FunctionComponent<Props> = ({ editState, profiles }) => {
  const [edit, setEdit] = editState;
  const toggleEdit = useCallback(() => setEdit(!edit), [edit, setEdit]);

  const profileOptions = useMemo<SelectorOption<LanguagesProfile>[]>(
    () =>
      profiles.map((v) => {
        return { label: v.name, value: v };
      }),
    [profiles]
  );

  if (edit) {
    return (
      <React.Fragment>
        <ContentHeader.Group pos="start">
          <Selector
            className="w-75"
            clearable
            options={profileOptions}
            label={(v) => v.name}
          ></Selector>
        </ContentHeader.Group>
        <ContentHeader.Group pos="end">
          <ContentHeader.Button icon={faUndo} onClick={toggleEdit}>
            Cancel
          </ContentHeader.Button>
          <ContentHeader.Button icon={faCheck}>Save</ContentHeader.Button>
        </ContentHeader.Group>
      </React.Fragment>
    );
  } else {
    return (
      <ContentHeader.Button icon={faList} onClick={toggleEdit}>
        Mass Edit
      </ContentHeader.Button>
    );
  }
};

export default connect(mapStateToProps)(EditModeHeader);
