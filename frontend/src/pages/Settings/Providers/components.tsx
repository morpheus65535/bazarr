import {
  Fragment,
  FunctionComponent,
  JSX,
  useCallback,
  useMemo,
  useRef,
  useState,
} from "react";
import {
  AutocompleteProps,
  Button,
  Divider,
  Group,
  SimpleGrid,
  Stack,
  Text as MantineText,
} from "@mantine/core";
import { useForm } from "@mantine/form";
import { capitalize } from "lodash";
import { Selector } from "@/components";
import { useModals, withModal } from "@/modules/modals";
import {
  Card,
  Check,
  Chips,
  Message,
  Password,
  ProviderTestButton,
  Selector as GlobalSelector,
  Text,
} from "@/pages/Settings/components";
import {
  FormContext,
  FormValues,
  runHooks,
  useFormActions,
  useStagedValues,
} from "@/pages/Settings/utilities/FormValues";
import { useSettingValue } from "@/pages/Settings/utilities/hooks";
import {
  SettingsProvider,
  useSettings,
} from "@/pages/Settings/utilities/SettingsProvider";
import { BuildKey, useSelectorOptions } from "@/utilities";
import { ASSERT } from "@/utilities/console";
import { ProviderInfo, ProviderList } from "./list";

type SettingsKey =
  | "settings-general-enabled_providers"
  | "settings-general-enabled_integrations";

interface ProviderViewProps {
  availableOptions: Readonly<ProviderInfo[]>;
  settingsKey: SettingsKey;
}

interface ProviderSelect {
  value: string;
  payload: ProviderInfo;
}

export const ProviderView: FunctionComponent<ProviderViewProps> = ({
  availableOptions,
  settingsKey,
}) => {
  const settings = useSettings();
  const staged = useStagedValues();
  const providers = useSettingValue<string[]>(settingsKey);

  const { update } = useFormActions();

  const modals = useModals();

  const select = useCallback(
    (v?: ProviderInfo) => {
      if (settings) {
        modals.openContextModal(ProviderModal, {
          payload: v ?? null,
          enabledProviders: providers ?? [],
          staged,
          settings,
          onChange: update,
          availableOptions: availableOptions,
          settingsKey: settingsKey,
        });
      }
    },
    [
      modals,
      providers,
      settings,
      staged,
      update,
      availableOptions,
      settingsKey,
    ],
  );

  const cards = useMemo(() => {
    if (providers) {
      return providers
        .flatMap((v) => {
          const item = availableOptions.find((inn) => inn.key === v);
          if (item) {
            return item;
          } else {
            return [];
          }
        })
        .map((v, idx) => (
          <Card
            titleStyles={{ overflow: "hidden", textOverflow: "ellipsis" }}
            key={BuildKey(v.key, idx)}
            header={v.name ?? capitalize(v.key)}
            description={v.description}
            onClick={() => select(v)}
            lineClamp={2}
          ></Card>
        ));
    } else {
      return [];
    }
  }, [providers, select, availableOptions]);

  return (
    <SimpleGrid cols={3}>
      {cards}
      <Card plus onClick={() => select()}></Card>
    </SimpleGrid>
  );
};

interface ProviderToolProps {
  payload: ProviderInfo | null;
  // TODO: Find a better solution to pass this info to modal
  enabledProviders: readonly string[];
  staged: LooseObject;
  settings: Settings;
  onChange: (v: LooseObject) => void;
  availableOptions: Readonly<ProviderInfo[]>;
  settingsKey: Readonly<SettingsKey>;
}

const SelectItem: AutocompleteProps["renderOption"] = ({ option }) => {
  const provider = option as ProviderSelect;

  return (
    <Stack gap={1}>
      <MantineText size="md">{provider.value}</MantineText>
      <MantineText size="xs">{provider.payload.description}</MantineText>
    </Stack>
  );
};

const validation = ProviderList.map((provider) => {
  return provider.inputs
    ?.map((input) => {
      if (input.validation === undefined) {
        return null;
      }

      return {
        [`settings-${provider.key}-${input.key}`]: input.validation?.rule,
      };
    })
    .filter((input) => input && Object.keys(input).length > 0)
    .reduce((acc, curr) => {
      return { ...acc, ...curr };
    }, {});
})
  .filter((provider) => provider && Object.keys(provider).length > 0)
  .reduce((acc, item) => {
    return { ...acc, ...item };
  }, {});

const ProviderTool: FunctionComponent<ProviderToolProps> = ({
  payload,
  enabledProviders,
  staged,
  settings,
  onChange,
  availableOptions,
  settingsKey,
}) => {
  const modals = useModals();

  const onChangeRef = useRef(onChange);
  onChangeRef.current = onChange;

  const [info, setInfo] = useState<Nullable<ProviderInfo>>(payload);

  const form = useForm<FormValues>({
    initialValues: {
      settings: staged,
      hooks: {},
    },
    validate: {
      settings: validation!,
    },
  });

  const deletePayload = useCallback(() => {
    if (payload && enabledProviders) {
      const idx = enabledProviders.findIndex((v) => v === payload.key);
      if (idx !== -1) {
        const newProviders = [...enabledProviders];
        newProviders.splice(idx, 1);
        onChangeRef.current({ [settingsKey]: newProviders });
        modals.closeAll();
      }
    }
  }, [payload, enabledProviders, modals, settingsKey]);

  const submit = useCallback(
    (values: FormValues) => {
      const result = form.validate();

      if (result.hasErrors) {
        return;
      }

      if (info && enabledProviders) {
        const changes = { ...values.settings };
        const hooks = values.hooks;

        // Add this provider if not exist
        if (enabledProviders.find((v) => v === info.key) === undefined) {
          changes[settingsKey] = [...enabledProviders, info.key];
        }

        // Apply submit hooks
        runHooks(hooks, changes);

        onChangeRef.current(changes);
        modals.closeAll();
      }
    },
    [info, enabledProviders, modals, settingsKey, form],
  );

  const canSave = info !== null;

  const onSelect = useCallback((item: Nullable<ProviderInfo>) => {
    if (item) {
      setInfo(item);
    } else {
      setInfo({
        key: "",
        description: "Unknown Provider",
      });
    }
  }, []);

  const options = useMemo(
    () =>
      availableOptions.filter(
        (v) =>
          enabledProviders?.find((p) => p === v.key && p !== info?.key) ===
          undefined,
      ),
    [info?.key, enabledProviders, availableOptions],
  );

  const selectorOptions = useSelectorOptions(
    options,
    (v) => v.name ?? capitalize(v.key),
  );

  const inputs = useMemo(() => {
    if (info === null || info.inputs === undefined) {
      return null;
    }

    const itemKey = info.key;

    const elements: JSX.Element[] = [];

    info.inputs?.forEach((value) => {
      const key = value.key;
      const label = value.name ?? capitalize(value.key);
      const options = value.options ?? [];

      const error = form.errors[`settings.settings-${itemKey}-${key}`] ? (
        <MantineText c="red" component="span" size="xs">
          {form.errors[`settings.settings-${itemKey}-${key}`]}
        </MantineText>
      ) : null;

      switch (value.type) {
        case "text":
          elements.push(
            <Fragment key={BuildKey(itemKey, key)}>
              <Text
                label={label}
                settingKey={`settings-${itemKey}-${key}`}
              ></Text>
              {error}
            </Fragment>,
          );
          return;
        case "password":
          elements.push(
            <Fragment key={BuildKey(itemKey, key)}>
              <Password
                label={label}
                settingKey={`settings-${itemKey}-${key}`}
              ></Password>
              {error}
            </Fragment>,
          );
          return;
        case "switch":
          elements.push(
            <Fragment key={BuildKey(itemKey, key)}>
              <Check
                inline
                label={label}
                settingKey={`settings-${itemKey}-${key}`}
              ></Check>
              {error}
            </Fragment>,
          );
          return;
        case "select":
          elements.push(
            <Fragment key={BuildKey(itemKey, key)}>
              <GlobalSelector
                label={label}
                settingKey={`settings-${itemKey}-${key}`}
                options={options}
              ></GlobalSelector>
              {error}
            </Fragment>,
          );
          return;
        case "testbutton":
          elements.push(
            <ProviderTestButton category={key}></ProviderTestButton>,
          );
          return;
        case "chips":
          elements.push(
            <Fragment key={BuildKey(itemKey, key)}>
              <Chips
                label={label}
                settingKey={`settings-${itemKey}-${key}`}
              ></Chips>
              {error}
            </Fragment>,
          );
          return;
        default:
          ASSERT(false, "Implement your new input here");
      }
    });

    return <Stack gap="xs">{elements}</Stack>;
  }, [info, form]);

  return (
    <SettingsProvider value={settings}>
      <FormContext.Provider value={form}>
        <Stack>
          <Stack gap="xs">
            <Selector
              data-autofocus
              searchable
              placeholder="Click to Select a Provider"
              renderOption={SelectItem}
              disabled={payload !== null}
              {...selectorOptions}
              value={info}
              onChange={onSelect}
            ></Selector>
            <Message>{info?.description}</Message>
            {inputs}
            <div hidden={info?.message === undefined}>
              <Message>{info?.message}</Message>
            </div>
          </Stack>
          <Divider></Divider>
          <Group justify="right">
            <Button hidden={!payload} color="red" onClick={deletePayload}>
              Disable
            </Button>
            <Button
              disabled={!canSave}
              onClick={() => {
                submit(form.values);
              }}
            >
              Enable
            </Button>
          </Group>
        </Stack>
      </FormContext.Provider>
    </SettingsProvider>
  );
};

const ProviderModal = withModal(ProviderTool, "provider-tool", {
  title: "Provider",
  size: "calc(50vw)",
});
