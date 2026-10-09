import { FunctionComponent } from "react";
import {
  Check,
  CollapseBox,
  Layout,
  Message,
  Section,
  Selector,
  Text,
} from "@/pages/Settings/components";
import {
  embeddedSubtitlesParserOption,
  folderOptions,
  hiExtensionOptions,
} from "./options";

const SettingsSubtitlesFilesView: FunctionComponent = () => {
  return (
    <Layout name="Subtitles">
      <Section header="Subtitle File Options">
        <Selector
          label="Subtitle Folder"
          options={folderOptions}
          settingKey="settings-general-subfolder"
        ></Selector>
        <Message>
          Choose the folder you wish to store/read the subtitles.
        </Message>
        <CollapseBox
          settingKey="settings-general-subfolder"
          on={(k) => k !== "" && k !== "current"}
        >
          <Text
            label="Custom Subtitles Folder"
            settingKey="settings-general-subfolder_custom"
          ></Text>
        </CollapseBox>
        <Selector
          label="Hearing-impaired subtitles extension"
          options={hiExtensionOptions}
          settingKey="settings-general-hi_extension"
          allowDeselect={false}
        ></Selector>
        <Message>
          What file extension to use when saving hearing-impaired subtitles to
          disk (e.g., video.en.sdh.srt).
        </Message>
        <Check
          label="Encode Subtitles To UTF-8"
          settingKey="settings-general-utf8_encode"
        ></Check>
        <Message>
          Re-encode downloaded subtitles to UTF-8. Should be left enabled in
          most cases.
        </Message>
        <Check
          label="Change Subtitle File Permission After Download (chmod)"
          settingKey="settings-general-chmod_enabled"
        ></Check>
        <CollapseBox indent settingKey="settings-general-chmod_enabled">
          <Text placeholder="0777" settingKey="settings-general-chmod"></Text>
          <Message>
            Must be a 4 digit octal number. Only for non-Windows systems.
          </Message>
        </CollapseBox>
      </Section>
      <Section header="Embedded Subtitles Handling">
        <Check
          label="Enable .strm Support"
          settingKey="settings-general-enable_strm_support"
        ></Check>
        <Message>
          Enable support for .strm files. Bazarr will read the stream URL from
          the file and analyze it for embedded tracks.
        </Message>
        <Check
          label="Treat Embedded Subtitles as Downloaded"
          settingKey="settings-general-use_embedded_subs"
        ></Check>
        <Message>
          Treat embedded subtitles in media files as already downloaded when
          determining missing ones.
        </Message>
        <CollapseBox indent settingKey="settings-general-use_embedded_subs">
          <Selector
            settingKey="settings-general-embedded_subtitles_parser"
            settingOptions={{
              onSaved: (v) => (v === undefined ? "ffprobe" : v),
            }}
            options={embeddedSubtitlesParserOption}
          ></Selector>
          <Message>Embedded Subtitles video parser.</Message>
          <Check
            label="Ignore Embedded PGS Subtitles"
            settingKey="settings-general-ignore_pgs_subs"
          ></Check>
          <Message>
            Ignore PGS Subtitles when detecting embedded subtitles.
          </Message>
          <Check
            label="Ignore Embedded VobSub Subtitles"
            settingKey="settings-general-ignore_vobsub_subs"
          ></Check>
          <Message>
            Ignore VobSub Subtitles when detecting embedded subtitles.
          </Message>
          <Check
            label="Ignore Embedded ASS Subtitles"
            settingKey="settings-general-ignore_ass_subs"
          ></Check>
          <Message>
            Ignore ASS Subtitles when detecting embedded subtitles.
          </Message>
          <Check
            label="Show Only Desired Languages"
            settingKey="settings-general-embedded_subs_show_desired"
          ></Check>
          <Message>
            Hide Embedded Subtitles for languages that are not currently
            desired.
          </Message>
        </CollapseBox>
      </Section>
    </Layout>
  );
};

export default SettingsSubtitlesFilesView;
