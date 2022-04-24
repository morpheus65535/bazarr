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
import { capitalize, isBoolean } from "lodash";
import {
  forwardRef,
  FunctionComponent,
  useCallback,
  useMemo,
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
import { useFormActions } from "../utilities/FormValues";
import { ProviderInfo, ProviderList } from "./list";

const ProviderKey = "settings-general-enabled_providers";

export const ProviderView: FunctionComponent = () => {
  const providers = useSettingValue<string[]>(ProviderKey);

  const modals = useModals();

  const select = useCallback(
    (v?: ProviderInfo) => {
      modals.openContextModal(ProviderModal, { payload: v ?? null });
    },
    [modals]
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
      <Card plus onClick={select}></Card>
    </SimpleGrid>
  );
};

interface ProviderToolProps {
  payload: ProviderInfo | null;
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

const ProviderTool: FunctionComponent<ProviderToolProps> = ({ payload }) => {
  const [staged, setChange] = useState<LooseObject>({});

  const modals = useModals();

  const [info, setInfo] = useState<Nullable<ProviderInfo>>(payload);

  const providers = useSettingValue<string[]>(ProviderKey);

  const { update } = useFormActions();

  const deletePayload = useCallback(() => {
    if (payload && providers) {
      const idx = providers.findIndex((v) => v === payload.key);
      if (idx !== -1) {
        const newProviders = [...providers];
        newProviders.splice(idx, 1);
        update({ [ProviderKey]: newProviders });
        modals.closeAll();
      }
    }
  }, [payload, providers, update, modals]);

  const addProvider = useCallback(() => {
    if (info && providers) {
      const changes = { ...staged };

      // Add this provider if not exist
      if (providers.find((v) => v === info.key) === undefined) {
        const newProviders = [...providers, info.key];
        changes[ProviderKey] = newProviders;
      }

      update(changes);
      modals.closeAll();
    }
  }, [info, providers, staged, update, modals]);

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
          providers?.find((p) => p === v.key && p !== info?.key) === undefined
      ),
    [info?.key, providers]
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
    // <StagedChangesContext.Provider value={[staged, setChange]}>
    <Stack>
      <Stack spacing="xs">
        <Selector
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
      <Group>
        <Button hidden={!payload} color="danger" onClick={deletePayload}>
          Delete
        </Button>
        <Button disabled={!canSave} onClick={addProvider}>
          Save
        </Button>
      </Group>
    </Stack>
    // </StagedChangesContext.Provider>
  );
};

const ProviderModal = withModal(ProviderTool, "provider-tool", {
  title: "Provider",
});
