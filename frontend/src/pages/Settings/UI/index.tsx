import { FunctionComponent } from "react";
import { Button } from "@mantine/core";
import { faGraduationCap } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { useOnboarding } from "@/contexts/Onboarding";
import {
  Layout,
  Message,
  Section,
  Selector,
} from "@/pages/Settings/components";
import { uiPageSizeKey } from "@/utilities/storage";
import {
  colorSchemeOptions,
  pageSizeOptions,
  showLiveBadgeOption,
} from "./options";

const SettingsUIView: FunctionComponent = () => {
  const { startTour } = useOnboarding();

  return (
    <Layout name="UI">
      <Section header="Onboarding">
        <Message>
          Replay the guided tour that walks through connecting Sonarr and
          Radarr, choosing subtitle languages and providers, and applying a
          language profile to your library.
        </Message>
        <Button
          type="button"
          variant="light"
          leftSection={<FontAwesomeIcon icon={faGraduationCap} />}
          onClick={startTour}
          w="fit-content"
        >
          Restart guided setup
        </Button>
      </Section>
      <Section header="List View">
        <Selector
          label="Page Size"
          options={pageSizeOptions}
          settingKey={uiPageSizeKey}
          defaultValue={50}
        ></Selector>
      </Section>
      <Section header="Style">
        <Selector
          label="Theme"
          options={colorSchemeOptions}
          settingKey="settings-general-theme"
          defaultValue={"auto"}
        ></Selector>
      </Section>
      <Section header="Badge Display">
        <Selector
          label="Show Live Badge"
          options={showLiveBadgeOption}
          settingKey="settings-general-show_live_badge"
          defaultValue={"auto"}
        ></Selector>
        <Message>
          Controls whether the “LIVE” badge appears when SignalR is connected.
          Turn this off if you prefer a cleaner interface. The “DOWN” badge will
          always appear when SignalR is disconnected, regardless of this
          setting. This option affects badge visibility only, not the actual
          connection status.
        </Message>
      </Section>
    </Layout>
  );
};

export default SettingsUIView;
