import { Selector } from "@/components";
import { useModals, withModal } from "@/modules/modals";
import { BuildKey, isReactText, useSelectorOptions } from "@/utilities";
import {
  Button,
  Divider,
  Group,
  SimpleGrid,
  Stack,
  Text as MantineText,
} from "@mantine/core";
import { useForm } from "@mantine/hooks";
import { capitalize, isBoolean } from "lodash";
import {
  forwardRef,
  FunctionComponent,
  useCallback,
  useMemo,
  useRef,
  useState,
} from "react";
import {
  Card,
  Check,
  Message,
  Password,
  Text,
  useSettingValue,
} from "../components";
import {
  FormContext,
  FormValues,
  useFormActions,
  useStagedValues,
} from "../utilities/FormValues";
import { SettingsProvider, useSettings } from "../utilities/SettingsProvider";
import { ProviderInfo, ProviderList } from "./list";

const ProviderKey = "settings-general-enabled_providers";

export const ProviderView: FunctionComponent = () => {
  const settings = useSettings();
  const staged = useStagedValues();
  const providers = useSettingValue<string[]>(ProviderKey);

  const { update } = useFormActions();

  const modals = useModals();

  const select = useCallback(
    (v?: ProviderInfo) => {
      modals.openContextModal(ProviderModal, {
        payload: v ?? null,
        enabledProviders: providers ?? [],
        staged,
        settings,
        onChange: update,
      });
    },
    [modals, providers, settings, staged, update]
  );

  const cards = useMemo(() => {
    if (providers) {
      return providers
        .flatMap((v) => {
          const item = ProviderList.find((inn) => inn.key === v);
          if (item) {
            return item;
          } else {
            return [];
          }
        })
        .map((v, idx) => (
          <Card
            key={BuildKey(v.key, idx)}
            header={v.name ?? capitalize(v.key)}
            description={v.description}
            onClick={() => select(v)}
          ></Card>
        ));
    } else {
      return [];
    }
  }, [providers, select]);

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
}

const SelectItem = forwardRef<
  HTMLDivElement,
  { payload: ProviderInfo; label: string }
>(({ payload: { description }, label, ...other }, ref) => {
  return (
    <Stack spacing={1} ref={ref} {...other}>
      <MantineText size="md">{label}</MantineText>
      <MantineText size="xs">{description}</MantineText>
    </Stack>
  );
});

const ProviderTool: FunctionComponent<ProviderToolProps> = ({
  payload,
  enabledProviders,
  staged,
  settings,
  onChange,
}) => {
  const modals = useModals();

  const onChangeRef = useRef(onChange);
  onChangeRef.current = onChange;

  const [info, setInfo] = useState<Nullable<ProviderInfo>>(payload);

  const form = useForm<FormValues>({
    initialValues: {
      settings: staged,
      storages: {},
    },
  });

  const deletePayload = useCallback(() => {
    if (payload && enabledProviders) {
      const idx = enabledProviders.findIndex((v) => v === payload.key);
      if (idx !== -1) {
        const newProviders = [...enabledProviders];
        newProviders.splice(idx, 1);
        onChangeRef.current({ [ProviderKey]: newProviders });
        modals.closeAll();
      }
    }
  }, [payload, enabledProviders, modals]);

  const submit = useCallback(
    (values: FormValues) => {
      if (info && enabledProviders) {
        const changes = { ...values.settings };

        // Add this provider if not exist
        if (enabledProviders.find((v) => v === info.key) === undefined) {
          const newProviders = [...enabledProviders, info.key];
          changes[ProviderKey] = newProviders;
        }

        onChangeRef.current(changes);
        modals.closeAll();
      }
    },
    [info, enabledProviders, modals]
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

  const availableOptions = useMemo(
    () =>
      ProviderList.filter(
        (v) =>
          enabledProviders?.find((p) => p === v.key && p !== info?.key) ===
          undefined
      ),
    [info?.key, enabledProviders]
  );

  const options = useSelectorOptions(
    availableOptions,
    (v) => v.name ?? capitalize(v.key)
  );

  const modification = useMemo(() => {
    if (info === null) {
      return null;
    }

    const defaultKey = info.defaultKey;
    const override = info.keyNameOverride ?? {};
    if (defaultKey === undefined) {
      return null;
    }

    const itemKey = info.key;

    const elements: JSX.Element[] = [];
    const checks: JSX.Element[] = [];

    for (const key in defaultKey) {
      const value = defaultKey[key];
      let label = key;

      if (label in override) {
        label = override[label];
      } else {
        label = capitalize(key);
      }

      if (isReactText(value)) {
        if (key === "password") {
          elements.push(
            <Password
              key={BuildKey(itemKey, key)}
              label={label}
              settingKey={`settings-${itemKey}-${key}`}
            ></Password>
          );
        } else {
          elements.push(
            <Text
              key={BuildKey(itemKey, key)}
              label={label}
              settingKey={`settings-${itemKey}-${key}`}
            ></Text>
          );
        }
      } else if (isBoolean(value)) {
        checks.push(
          <Check
            key={key}
            inline
            label={label}
            settingKey={`settings-${itemKey}-${key}`}
          ></Check>
        );
      }
    }

    return (
      <Stack spacing="xs">
        {elements}
        <Group hidden={checks.length === 0}>{checks}</Group>
      </Stack>
    );
  }, [info]);

  return (
    <SettingsProvider value={settings}>
      <FormContext.Provider value={form}>
        <Stack>
          <Stack spacing="xs">
            <Selector
              searchable
              placeholder="Click to Select a Provider"
              itemComponent={SelectItem}
              disabled={payload !== null}
              {...options}
              value={info}
              onChange={onSelect}
            ></Selector>
            <Message>{info?.description}</Message>
            {modification}
            <div hidden={info?.message === undefined}>
              <Message>{info?.message}</Message>
            </div>
          </Stack>
          <Divider></Divider>
          <Group position="right">
            <Button hidden={!payload} color="red" onClick={deletePayload}>
              Delete
            </Button>
            <Button disabled={!canSave} onClick={form.onSubmit(submit)}>
              Save
            </Button>
          </Group>
        </Stack>
      </FormContext.Provider>
    </SettingsProvider>
  );
};

const ProviderModal = withModal(ProviderTool, "provider-tool", {
  title: "Provider",
});
