import { FunctionComponent } from "react";
import {
  Check,
  CollapseBox,
  Layout,
  Message,
  Section,
  Selector,
  Slider,
} from "@/pages/Settings/components";
import {
  adaptiveSearchingDelayOption,
  adaptiveSearchingDeltaOption,
} from "./options";

const SettingsSubtitlesSearchView: FunctionComponent = () => {
  return (
    <Layout name="Subtitles">
      <Section header="Upgrading Subtitles">
        <Check
          label="Upgrade Previously Downloaded Subtitles"
          settingKey="settings-general-upgrade_subs"
        ></Check>
        <Message>
          Schedule a task to upgrade subtitles previously downloaded by Bazarr.
        </Message>
        <CollapseBox settingKey="settings-general-upgrade_subs">
          <Slider
            settingKey="settings-general-days_to_upgrade_subs"
            max={30}
            mb="lg"
          ></Slider>
          <Message>
            Number of days to go back in history to upgrade subtitles.
          </Message>
          <Check
            label="Upgrade Manually Downloaded or Translated Subtitles"
            settingKey="settings-general-upgrade_manual"
          ></Check>
          <Message>
            Enable or disable upgrade of manually downloaded or translated
            subtitles.
          </Message>
        </CollapseBox>
      </Section>
      <Section header="Search Scores">
        <Slider
          label="Minimum Score For Episodes"
          settingKey="settings-general-minimum_score"
        ></Slider>
        <Slider
          label="Minimum Score For Movies"
          settingKey="settings-general-minimum_score_movie"
        ></Slider>
        <Message>
          Subtitles with a score below the minimum will not be downloaded
          automatically.
        </Message>
      </Section>
      <Section header="Performance / Optimization">
        <Check
          label="Adaptive Searching"
          settingKey="settings-general-adaptive_searching"
        ></Check>
        <Message>
          When enabled, Bazarr will skip searching providers for subtitles which
          have been searched recently.
        </Message>
        <CollapseBox settingKey="settings-general-adaptive_searching">
          <Selector
            settingKey="settings-general-adaptive_searching_delay"
            settingOptions={{ onSaved: (v) => (v === undefined ? "3w" : v) }}
            options={adaptiveSearchingDelayOption}
          ></Selector>
          <Message>
            The delay from the first search to adaptive searching taking effect.
            During this time window Bazarr will continue to search for
            subtitles, even if they have been searched for recently.
          </Message>
          <Selector
            settingKey="settings-general-adaptive_searching_delta"
            settingOptions={{ onSaved: (v) => (v === undefined ? "1w" : v) }}
            options={adaptiveSearchingDeltaOption}
          ></Selector>
          <Message>
            The delay between Bazarr searching for subtitles in adaptive search
            mode. If the media has been searched for more recently than this
            value, Bazarr will skip searching for subtitles.
          </Message>
        </CollapseBox>
        <Check
          label="Search Enabled Providers Simultaneously"
          settingKey="settings-general-multithreading"
        ></Check>
        <Message>
          Search multiple providers at once. (Don't choose this on low powered
          devices).
        </Message>
        <Check
          label="Skip video file hash calculation"
          settingKey="settings-general-skip_hashing"
        ></Check>
        <Message>
          Skip video file hashing during search process to prevent a sleeping
          hard disk drive from waking up. However, this may decrease your search
          results scores.
        </Message>
      </Section>
    </Layout>
  );
};

export default SettingsSubtitlesSearchView;
