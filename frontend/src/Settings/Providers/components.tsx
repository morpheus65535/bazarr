import { capitalize, isArray, isBoolean } from "lodash";
import React, {
  FunctionComponent,
  useCallback,
  useMemo,
  useState,
} from "react";
import { Button, Col, Container, Row } from "react-bootstrap";
import {
  BaseModal,
  Selector,
  useCloseModal,
  useOnModalShow,
  usePayload,
  useShowModal,
} from "../../components";
import { isReactText } from "../../utilites";
import {
  Check,
  ColCard,
  Message,
  StagedChangesContext,
  Text,
  useLatest,
  useMultiUpdate,
} from "../components";
import { ProviderInfo, ProviderList } from "./list";

const ModalKey = "provider-modal";
const ProviderKey = "settings-general-enabled_providers";

export const ProviderView: FunctionComponent = () => {
  const providers = useLatest<string[]>(ProviderKey, isArray);

  const showModal = useShowModal();

  const select = useCallback(
    (v?: ProviderInfo) => {
      showModal(ModalKey, v ?? null);
    },
    [showModal]
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
          <ColCard
            key={idx}
            header={v.name ?? capitalize(v.key)}
            subheader={v.description}
            onClick={() => select(v)}
          ></ColCard>
        ));
    } else {
      return [];
    }
  }, [providers, select]);

  return (
    <Container fluid>
      <Row>
        {cards}
        <ColCard key="add-card" plus onClick={select}></ColCard>
      </Row>
    </Container>
  );
};

export const ProviderModal: FunctionComponent = () => {
  const payload = usePayload<ProviderInfo>(ModalKey);

  const [staged, setChange] = useState<LooseObject>({});

  const [info, setInfo] = useState<Nullable<ProviderInfo>>(payload ?? null);

  const onShow = useCallback(() => setInfo(payload ?? null), [payload]);

  useOnModalShow(ModalKey, onShow);

  const providers = useLatest<string[]>(ProviderKey, isArray);

  const closeModal = useCloseModal();

  const updateGlobal = useMultiUpdate();

  const deletePayload = useCallback(() => {
    if (payload && providers) {
      const idx = providers.findIndex((v) => v === payload.key);
      if (idx !== -1) {
        const newProviders = [...providers];
        newProviders.splice(idx, 1);
        updateGlobal({ [ProviderKey]: newProviders });
        closeModal();
      }
    }
  }, [payload, providers, updateGlobal, closeModal]);

  const addProvider = useCallback(() => {
    if (info && providers) {
      const changes = { ...staged };

      // Add this provider if not exist
      if (providers.find((v) => v === info.key) === undefined) {
        const newProviders = [...providers, info.key];
        changes[ProviderKey] = newProviders;
      }

      updateGlobal(changes);
      closeModal();
    }
  }, [info, providers, staged, closeModal, updateGlobal]);

  const canSave = info !== null;

  const footer = useMemo(
    () => (
      <React.Fragment>
        <Button hidden={!payload} variant="danger" onClick={deletePayload}>
          Delete
        </Button>
        <Button disabled={!canSave} onClick={addProvider}>
          Save
        </Button>
      </React.Fragment>
    ),
    [canSave, payload, deletePayload, addProvider]
  );

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
          <Col key={key} xs={12} className="mt-2">
            <Text
              password={key === "password"}
              placeholder={visibleKey}
              settingKey={`settings-${itemKey}-${key}`}
            ></Text>
          </Col>
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
      <Row>
        {elements}
        <Col hidden={checks.length === 0} className="mt-2">
          {checks}
        </Col>
      </Row>
    );
  }, [info]);

  return (
    <BaseModal title="Provider" footer={footer} modalKey={ModalKey}>
      <StagedChangesContext.Provider value={[staged, setChange]}>
        <Container>
          <Row>
            <Col>
              <Selector
                disabled={payload !== null}
                options={options}
                value={info}
                label={(v) => v?.name ?? capitalize(v?.key ?? "")}
                onChange={onSelect}
              ></Selector>
            </Col>
          </Row>
          <Row>
            <Col className="mb-2">
              <Message>{info?.description}</Message>
            </Col>
          </Row>
          {modification}
          <Row hidden={info?.message === undefined}>
            <Col>
              <Message>{info?.message}</Message>
            </Col>
          </Row>
        </Container>
      </StagedChangesContext.Provider>
    </BaseModal>
  );
};
