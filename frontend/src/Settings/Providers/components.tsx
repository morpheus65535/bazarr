import { faPlus } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { capitalize, isArray, isBoolean } from "lodash";
import React, {
  FunctionComponent,
  useCallback,
  useMemo,
  useState,
} from "react";
import { Button, Card, Col, Container, Row } from "react-bootstrap";
import {
  BasicModal,
  Selector,
  useCloseModal,
  usePayload,
  useShowModal,
  useWhenModalShow,
} from "../../components";
import { isReactText } from "../../utilites";
import {
  Check,
  Group,
  Message,
  Text,
  UpdateChangeContext,
  useLatest,
  useUpdate,
} from "../components";
import { ProviderInfo, ProviderList } from "./list";
import "./style.scss";

const ModalKey = "provider-modal";
const ProviderKey = "settings-general-enabled_providers";

export const ProviderCard: FunctionComponent<{ providerKey?: string }> = ({
  providerKey,
}) => {
  const info = useMemo<ProviderInfo | undefined>(() => {
    if (providerKey) {
      const info = ProviderList.find((l) => l.key === providerKey);

      if (info) {
        return info;
      } else {
        return {
          key: providerKey,
          description: "Unknown Provider",
        };
      }
    } else {
      return undefined;
    }
  }, [providerKey]);

  const showModal = useShowModal();

  return (
    <Card className="provider-card" onClick={() => showModal(ModalKey, info)}>
      {info ? (
        <Card.Body>
          <Card.Title className="text-nowrap text-overflow-ellipsis">
            {info.name ?? capitalize(info.key)}
          </Card.Title>
          <Card.Subtitle className="small">{info.description}</Card.Subtitle>
        </Card.Body>
      ) : (
        <Card.Body className="d-flex justify-content-center align-items-center">
          <FontAwesomeIcon size="2x" icon={faPlus}></FontAwesomeIcon>
        </Card.Body>
      )}
    </Card>
  );
};

export const ProviderView: FunctionComponent = () => {
  const providers = useLatest<string[]>(ProviderKey, isArray);

  const cards = useMemo(() => {
    return [...(providers ?? []), undefined].map((v, idx) => (
      <Col className="p-2" xs={6} lg={4} key={idx}>
        <ProviderCard providerKey={v}></ProviderCard>
      </Col>
    ));
  }, [providers]);

  return (
    <Container fluid>
      <Row>{cards}</Row>
    </Container>
  );
};

export const ProviderModal: FunctionComponent = () => {
  const payload = usePayload<ProviderInfo | undefined>(ModalKey);

  const [staged, setChange] = useState<LooseObject>({});

  const [info, setInfo] = useState(payload);

  const providers = useLatest<string[]>(ProviderKey, isArray);

  const closeModal = useCloseModal();

  const updateGlobal = useUpdate();

  const updateLocal = useCallback(
    (v: any, key?: string) => {
      if (key) {
        staged[key] = v;

        if (process.env.NODE_ENV === "development") {
          console.log("modal stage settings", staged);
        }

        setChange({ ...staged });
      }
    },
    [staged]
  );

  const deletePayload = useCallback(() => {
    if (payload && providers) {
      const idx = providers.findIndex((v) => v === payload.key);
      if (idx !== -1) {
        providers.splice(idx, 1);
        updateGlobal([...providers], ProviderKey);
        closeModal();
      }
    }
  }, [payload, providers, updateGlobal, closeModal]);

  const addProvider = useCallback(() => {
    if (info && providers) {
      const changes = staged;
      providers.push(info.key);
      changes[ProviderKey] = [...providers];

      for (const key in changes) {
        const value = changes[key];
        updateGlobal(value, key);
      }

      closeModal();
    }
  }, [info, providers, staged, closeModal, updateGlobal]);

  useWhenModalShow(ModalKey, () => {
    setInfo(payload);
    setChange({});
  });

  const canSave = useMemo(() => {
    if (payload === undefined) {
      return info !== undefined;
    } else {
      return Object.keys(staged).length !== 0;
    }
  }, [payload, info, staged]);

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

  const onSelect = useCallback((item: ProviderInfo | undefined) => {
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
    if (info === undefined) {
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
    <BasicModal title="Provider" footer={footer} modalKey={ModalKey}>
      <UpdateChangeContext.Provider value={updateLocal}>
        <Container>
          <Row>
            <Col>
              <Selector
                disabled={payload !== undefined}
                options={options}
                value={payload}
                label={(v) => v.name ?? capitalize(v.key)}
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
      </UpdateChangeContext.Provider>
    </BasicModal>
  );
};

interface ProviderEditProps {
  providerKey: string;
}

export const ProviderSection: FunctionComponent<ProviderEditProps> = ({
  providerKey,
  children,
}) => {
  const info = useMemo(() => ProviderList.find((v) => v.key === providerKey), [
    providerKey,
  ]);

  const enabled = useLatest<string[]>(ProviderKey, isArray);

  const hide = useMemo(() => {
    if (enabled) {
      return enabled.findIndex((v) => v === providerKey) === -1;
    } else {
      return true;
    }
  }, [enabled, providerKey]);

  const header = useMemo(() => {
    const name = info?.name;

    if (name) {
      return name;
    } else {
      return capitalize(providerKey);
    }
  }, [providerKey, info]);

  return (
    <Group hidden={hide} header={header}>
      {children}
      {info && info.description && <Message>{info?.description}</Message>}
    </Group>
  );
};
