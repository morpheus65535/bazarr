import { Selector, SelectorOption } from "@/components";
import {
  useModal,
  useModalControl,
  usePayload,
  withModal,
} from "@/modules/modals";
import { isReactText } from "@/utilities";
import { Button, Group, SimpleGrid, Stack } from "@mantine/core";
import { capitalize, isArray, isBoolean } from "lodash";
import {
  FunctionComponent,
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";
import {
  Card,
  Check,
  Message,
  StagedChangesContext,
  Text,
  useLatest,
  useMultiUpdate,
} from "../components";
import { ProviderInfo, ProviderList } from "./list";

const ProviderKey = "settings-general-enabled_providers";

export const ProviderView: FunctionComponent = () => {
  const providers = useLatest<string[]>(ProviderKey, isArray);

  const { show } = useModalControl();

  const select = useCallback(
    (v?: ProviderInfo) => {
      show(ProviderModal, v ?? null);
    },
    [show]
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
            header={v.name ?? capitalize(v.key)}
            subheader={v.description}
            onClick={() => select(v)}
          ></Card>
        ));
    } else {
      return [];
    }
  }, [providers, select]);

  return (
    <>
      <SimpleGrid cols={3}>
        {cards}
        <Card plus onClick={select}></Card>
      </SimpleGrid>
      <ProviderModal></ProviderModal>
    </>
  );
};

const ProviderTool: FunctionComponent = () => {
  const payload = usePayload<ProviderInfo>();
  const Modal = useModal();
  const { hide } = useModalControl();

  const [staged, setChange] = useState<LooseObject>({});

  useEffect(() => {
    setInfo(payload);
  }, [payload]);

  const [info, setInfo] = useState<Nullable<ProviderInfo>>(payload);

  const providers = useLatest<string[]>(ProviderKey, isArray);

  const updateGlobal = useMultiUpdate();

  const deletePayload = useCallback(() => {
    if (payload && providers) {
      const idx = providers.findIndex((v) => v === payload.key);
      if (idx !== -1) {
        const newProviders = [...providers];
        newProviders.splice(idx, 1);
        updateGlobal({ [ProviderKey]: newProviders });
        hide();
      }
    }
  }, [payload, providers, updateGlobal, hide]);

  const addProvider = useCallback(() => {
    if (info && providers) {
      const changes = { ...staged };

      // Add this provider if not exist
      if (providers.find((v) => v === info.key) === undefined) {
        const newProviders = [...providers, info.key];
        changes[ProviderKey] = newProviders;
      }

      updateGlobal(changes);
      hide();
    }
  }, [info, providers, staged, updateGlobal, hide]);

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

  const options = useMemo<SelectorOption<ProviderInfo>[]>(
    () =>
      ProviderList.filter(
        (v) => providers?.find((p) => p === v.key) === undefined
      ).map((v) => ({
        label: v.name ?? capitalize(v.key),
        value: v,
      })),
    [providers]
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
      let visibleKey = key;

      if (visibleKey in override) {
        visibleKey = override[visibleKey];
      } else {
        visibleKey = capitalize(key);
      }

      if (isReactText(value)) {
        elements.push(
          <Text
            password={key === "password"}
            placeholder={visibleKey}
            settingKey={`settings-${itemKey}-${key}`}
          ></Text>
        );
      } else if (isBoolean(value)) {
        checks.push(
          <Check
            key={key}
            inline
            label={visibleKey}
            settingKey={`settings-${itemKey}-${key}`}
          ></Check>
        );
      }
    }

    return (
      <Stack>
        {elements}
        <Group hidden={checks.length === 0}>{checks}</Group>
      </Stack>
    );
  }, [info]);

  // const selectorComponents = useMemo<
  //   Partial<SelectorComponents<ProviderInfo, false>>
  // >(
  //   () => ({
  //     Option: ({ data, ...other }) => {
  //       const { label, value } = data;
  //       return (
  //         <components.Option data={data} {...other}>
  //           {label}
  //           <p className="small m-0 text-muted">{value.description}</p>
  //         </components.Option>
  //       );
  //     },
  //   }),
  //   []
  // );

  const getLabel = useCallback(
    (v: ProviderInfo) => v.name ?? capitalize(v.key),
    []
  );

  const footer = (
    <>
      <Button hidden={!payload} color="danger" onClick={deletePayload}>
        Delete
      </Button>
      <Button disabled={!canSave} onClick={addProvider}>
        Save
      </Button>
    </>
  );

  return (
    <Modal title="Provider" footer={footer}>
      <StagedChangesContext.Provider value={[staged, setChange]}>
        <Stack>
          <Selector
            // components={selectorComponents}
            disabled={payload !== null}
            options={options}
            value={info}
            getKey={getLabel}
            onChange={onSelect}
          ></Selector>

          <Message>{info?.description}</Message>
          {modification}
          <div hidden={info?.message === undefined}>
            <Message>{info?.message}</Message>
          </div>
        </Stack>
      </StagedChangesContext.Provider>
    </Modal>
  );
};

const ProviderModal = withModal(ProviderTool, "provider-tool");
