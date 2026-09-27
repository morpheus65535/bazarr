import { Anchor, Code, List, Text } from "@mantine/core";
import {
  faCircleCheck,
  faClosedCaptioning,
  faFilm,
  faFolderTree,
  faGlobe,
  faLanguage,
  faLayerGroup,
  faNetworkWired,
  faPlay,
  faPowerOff,
  faWandMagicSparkles,
} from "@fortawesome/free-solid-svg-icons";
import { TourStep } from "@/components/tour";

const wikiGuideUrl = "https://wiki.bazarr.media/Getting-Started/Setup-Guide/";
const wikiFirstRunUrl =
  "https://wiki.bazarr.media/Getting-Started/First-time-installation-configuration/";
const hardlinksUrl =
  "https://trash-guides.info/File-and-Folder-Structure/Hardlinks-and-Instant-Moves/";

// The Settings pages render their Save button with this marker so the tour can
// spotlight it alongside the relevant section.
const saveTarget = '[data-onboarding="settings-save"]';

/**
 * The first-run tour. Every step maps to a section of the official setup guide
 * so the wording matches what users read on the wiki. The settings steps are
 * interactive: the page stays usable and the tour only guides and highlights.
 */
export const onboardingSteps: TourStep[] = [
  {
    id: "welcome",
    title: "Welcome to Bazarr",
    icon: faWandMagicSparkles,
    description: (
      <>
        <Text size="sm">
          Bazarr downloads the subtitles you want for the series and movies
          managed by Sonarr and Radarr. This short tour covers the settings to
          get running first.
        </Text>
        <Text size="sm" mt="xs">
          You can skip it at any time and restart it later from Settings → UI.
        </Text>
      </>
    ),
  },
  {
    id: "sonarr-enable",
    title: "Enable Sonarr",
    icon: faPowerOff,
    route: "/settings/library/sonarr",
    target: '[data-testid="section-Use Sonarr"]',
    secondaryTargets: [saveTarget],
    placement: "bottom",
    interactive: true,
    optional: true,
    autoAdvanceMs: 30000,
    description: (
      <Text size="sm">
        Turn Sonarr on and save. The host details appear once it is enabled, and
        Bazarr will manage subtitles for the series Sonarr manages.
      </Text>
    ),
  },
  {
    id: "sonarr-host",
    title: "Connect Sonarr",
    icon: faNetworkWired,
    route: "/settings/library/sonarr",
    target: '[data-testid="section-Host"]',
    secondaryTargets: [saveTarget],
    placement: "bottom",
    interactive: true,
    optional: true,
    autoAdvanceMs: 30000,
    description: (
      <>
        <Text size="sm">
          Enter the address, port and API key of your Sonarr, click <b>Test</b>{" "}
          to confirm, then save.
        </Text>
        <Text size="sm" mt="xs" c="dimmed">
          Running Bazarr in Docker? Don't use <Code>localhost</Code> to reach
          Sonarr on the same host - use the container name or host IP.
        </Text>
      </>
    ),
  },
  {
    id: "path-mappings-sonarr",
    title: "Sonarr path mappings",
    icon: faFolderTree,
    route: "/settings/library/sonarr",
    target: '[data-testid="section-Path Mappings"]',
    secondaryTargets: [saveTarget],
    placement: "top",
    interactive: true,
    optional: true,
    advanceOnAction: "secondary",
    autoAdvanceMs: 30000,
    description: (
      <>
        <Text size="sm">
          Only needed if Sonarr and Bazarr see the same files under different
          paths (for example when they run in separate containers). Map the path
          Sonarr uses to the path Bazarr uses.
        </Text>
        <Text size="sm" mt="xs" c="dimmed">
          If both sides use identical paths, leave this empty - a mapping with
          the same values on both sides causes errors. See the{" "}
          <Anchor href={hardlinksUrl} target="_blank" rel="noreferrer">
            hardlinks guide
          </Anchor>
          .
        </Text>
      </>
    ),
  },
  {
    id: "radarr-enable",
    title: "Enable Radarr",
    icon: faPowerOff,
    route: "/settings/library/radarr",
    target: '[data-testid="section-Use Radarr"]',
    secondaryTargets: [saveTarget],
    placement: "bottom",
    interactive: true,
    optional: true,
    autoAdvanceMs: 30000,
    blockedMessage: (
      <Text size="sm">
        Bazarr needs at least one of Sonarr or Radarr. Enable one and save to
        continue.
      </Text>
    ),
    description: (
      <Text size="sm">
        Do the same for Radarr to manage subtitles for your movies. The host
        details appear once it is enabled.
      </Text>
    ),
  },
  {
    id: "radarr-host",
    title: "Connect Radarr",
    icon: faNetworkWired,
    route: "/settings/library/radarr",
    target: '[data-testid="section-Host"]',
    secondaryTargets: [saveTarget],
    placement: "bottom",
    interactive: true,
    optional: true,
    autoAdvanceMs: 30000,
    description: (
      <>
        <Text size="sm">
          Enter the address, port and API key of your Radarr. The default port
          is <Code>7878</Code>. Test it, then save.
        </Text>
        <Text size="sm" mt="xs" c="dimmed">
          Sonarr and Radarr are independent - you can set up the other one
          later.
        </Text>
      </>
    ),
  },
  {
    id: "path-mappings-radarr",
    title: "Radarr path mappings",
    icon: faFolderTree,
    route: "/settings/library/radarr",
    target: '[data-testid="section-Path Mappings"]',
    secondaryTargets: [saveTarget],
    placement: "top",
    interactive: true,
    optional: true,
    advanceOnAction: "secondary",
    autoAdvanceMs: 30000,
    description: (
      <Text size="sm">
        Same as Sonarr: add a mapping only when Radarr and Bazarr access the
        same files through different paths. Otherwise leave it empty and save.
      </Text>
    ),
  },
  {
    id: "languages",
    title: "Choose your subtitle languages",
    icon: faLanguage,
    route: "/settings/languages/general",
    target: '[data-testid="section-Subtitles Language"]',
    secondaryTargets: [saveTarget],
    placement: "bottom",
    interactive: true,
    optional: true,
    autoAdvanceMs: 30000,
    description: (
      <>
        <Text size="sm">
          Pick every language you want subtitles for, then Save. These become
          the building blocks for the language profiles in the next step.
        </Text>
        <Text size="sm" mt="xs" c="dimmed">
          Leave Single Language off unless your media player cannot read the
          language code in subtitle filenames.
        </Text>
      </>
    ),
  },
  {
    id: "profiles",
    title: "Build a language profile",
    icon: faLayerGroup,
    route: "/settings/languages/profiles",
    target: '[data-testid="section-Languages Profile"]',
    secondaryTargets: [saveTarget],
    placement: "bottom",
    interactive: true,
    autoAdvanceMs: 30000,
    blockedMessage: (
      <Text size="sm">
        Create at least one language profile and save it to continue.
      </Text>
    ),
    description: (
      <>
        <Text size="sm">
          A language profile decides which languages Bazarr looks for, in
          priority order, and whether it wants forced or hearing-impaired
          tracks. Add one here, then Save.
        </Text>
        <List size="sm" spacing={4} mt="xs">
          <List.Item>
            Add the languages you enabled in the previous step.
          </List.Item>
          <List.Item>
            Set a cutoff to stop searching once a preferred language is found.
          </List.Item>
          <List.Item>
            Turn on the default profile to apply it automatically to new
            content.
          </List.Item>
        </List>
      </>
    ),
  },
  {
    id: "providers",
    title: "Enable subtitle providers",
    icon: faGlobe,
    route: "/settings/providers/subtitles",
    target: '[data-testid="section-Enabled Providers"]',
    secondaryTargets: [saveTarget],
    placement: "bottom",
    interactive: true,
    autoAdvanceMs: 30000,
    blockedMessage: (
      <Text size="sm">
        Enable at least one subtitle provider and save it to continue.
      </Text>
    ),
    description: (
      <>
        <Text size="sm">
          Providers are where subtitles actually come from. Click the{" "}
          <b>+ card</b> to enable a provider, then click an enabled provider to
          add its credentials (account or API key).
        </Text>
        <Text size="sm" mt="xs" c="dimmed">
          The page stays usable during this step, so you can set everything up
          right here. Use the highlighted Save when done.
        </Text>
      </>
    ),
  },
  {
    id: "subtitles",
    title: "Fine-tune subtitle handling",
    icon: faClosedCaptioning,
    route: "/settings/subtitles/files",
    target: '[data-testid="section-Subtitle File Options"]',
    secondaryTargets: [saveTarget],
    placement: "bottom",
    interactive: true,
    optional: true,
    advanceOnAction: "secondary",
    autoAdvanceMs: 30000,
    description: (
      <>
        <Text size="sm">
          Choose where subtitles are saved (AlongSide Media File is recommended)
          and review how embedded subtitles are treated, then Save.
        </Text>
        <Text size="sm" mt="xs" c="dimmed">
          Use the tabs on this page to enable automatic subtitle synchronization
          under Processing, so out-of-sync subtitles get corrected.
        </Text>
      </>
    ),
  },
  {
    id: "library-movies-select",
    title: "Select your movies",
    icon: faFilm,
    route: "/movies",
    target: '[data-onboarding="media-select"]',
    placement: "bottom",
    interactive: true,
    optional: true,
    advanceOnAction: "primary",
    description: (
      <Text size="sm">
        Click <b>Select</b> to start choosing movies.
      </Text>
    ),
  },
  {
    id: "library-movies-choose",
    title: "Choose which movies",
    icon: faFilm,
    route: "/movies",
    target: '[data-onboarding="media-bulk"]',
    secondaryTargets: ['[data-onboarding="media-checkbox"]'],
    placement: "bottom",
    interactive: true,
    optional: true,
    advanceWhenPresent: '[data-onboarding="media-selected"]',
    description: (
      <Text size="sm">
        Select the movies to update: <b>Select all matching filters</b>,{" "}
        <b>Select all on this page</b>, or tick individual movies.
      </Text>
    ),
  },
  {
    id: "library-movies-profile",
    title: "Choose the profile",
    icon: faLayerGroup,
    route: "/movies",
    target: '[data-onboarding="media-profile"]',
    placement: "bottom",
    interactive: true,
    optional: true,
    advanceWhenPresent: '[data-onboarding="profile-staged"]',
    description: (
      <Text size="sm">
        Pick the language profile to apply under <b>Change Profile</b>.
      </Text>
    ),
  },
  {
    id: "library-movies-save",
    title: "Save the new profile",
    icon: faCircleCheck,
    route: "/movies",
    target: '[data-onboarding="media-save"]',
    placement: "bottom",
    interactive: true,
    optional: true,
    advanceOnAction: "primary",
    description: (
      <Text size="sm">
        Click <b>Save</b> to apply the profile to the selected movies.
      </Text>
    ),
  },
  {
    id: "library-series-select",
    title: "Select your series",
    icon: faPlay,
    route: "/series",
    target: '[data-onboarding="media-select"]',
    placement: "bottom",
    interactive: true,
    optional: true,
    advanceOnAction: "primary",
    description: (
      <Text size="sm">
        Now do the same for your series: click <b>Select</b>.
      </Text>
    ),
  },
  {
    id: "library-series-choose",
    title: "Choose which series",
    icon: faPlay,
    route: "/series",
    target: '[data-onboarding="media-bulk"]',
    secondaryTargets: ['[data-onboarding="media-checkbox"]'],
    placement: "bottom",
    interactive: true,
    optional: true,
    advanceWhenPresent: '[data-onboarding="media-selected"]',
    description: (
      <Text size="sm">
        Select the series to update: <b>Select all matching filters</b>,{" "}
        <b>Select all on this page</b>, or tick individual series.
      </Text>
    ),
  },
  {
    id: "library-series-profile",
    title: "Choose the profile",
    icon: faLayerGroup,
    route: "/series",
    target: '[data-onboarding="media-profile"]',
    placement: "bottom",
    interactive: true,
    optional: true,
    advanceWhenPresent: '[data-onboarding="profile-staged"]',
    description: (
      <Text size="sm">
        Pick the language profile to apply under <b>Change Profile</b>.
      </Text>
    ),
  },
  {
    id: "library-series-save",
    title: "Save the new profile",
    icon: faCircleCheck,
    route: "/series",
    target: '[data-onboarding="media-save"]',
    placement: "bottom",
    interactive: true,
    optional: true,
    advanceOnAction: "primary",
    description: (
      <Text size="sm">
        Click <b>Save</b> to apply the profile to the selected series.
      </Text>
    ),
  },
  {
    id: "done",
    title: "You're all set",
    icon: faCircleCheck,
    description: (
      <>
        <Text size="sm">
          Bazarr keeps scanning in the background - new episodes and movies get
          subtitles automatically based on your profile.
        </Text>
        <Text size="sm" mt="xs">
          Need a deeper walkthrough? See the{" "}
          <Anchor href={wikiGuideUrl} target="_blank" rel="noreferrer">
            setup guide
          </Anchor>{" "}
          and the{" "}
          <Anchor href={wikiFirstRunUrl} target="_blank" rel="noreferrer">
            first-time configuration
          </Anchor>{" "}
          pages.
        </Text>
      </>
    ),
  },
];
