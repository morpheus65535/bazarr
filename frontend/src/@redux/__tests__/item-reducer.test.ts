import {
  configureStore,
  createAction,
  createAsyncThunk,
  createReducer,
} from "@reduxjs/toolkit";
import {} from "jest";
import { defaultState, TestType } from "../tests/helper";
import { createAsyncItemReducer } from "../utils/factory";

// Item
const defaultItem: TestType = { id: 0, name: "test" };
const allResolved = createAsyncThunk("all/resolved", () => {
  return new Promise<TestType>((resolve) => {
    resolve(defaultItem);
  });
});
const allRejected = createAsyncThunk("all/rejected", () => {
  return new Promise<TestType>((resolve, rejected) => {
    rejected("Error");
  });
});
const dirty = createAction("dirty/ids");

const reducer = createReducer(defaultState, (builder) => {
  createAsyncItemReducer(builder, (s) => s.item, { all: allResolved, dirty });
  createAsyncItemReducer(builder, (s) => s.item, { all: allRejected });
});

function createStore() {
  const store = configureStore({
    reducer,
  });
  expect(store.getState()).toEqual(defaultState);
  return store;
}

let store = createStore();

function use(callback: (entities: Async.Item<TestType>) => void) {
  const item = store.getState().item;
  callback(item);
}

// Begin Test Section

beforeEach(() => {
  store = createStore();
});

it("item loading", async () => {
  return new Promise<void>((done) => {
    store.dispatch(allResolved()).finally(() => {
      use((item) => {
        expect(item.error).toBeNull();
        expect(item.content).toEqual(defaultItem);
      });
      done();
    });
    use((item) => {
      expect(item.state).toBe("loading");
      expect(item.error).toBeNull();
      expect(item.content).toBeNull();
    });
  });
});

it("item uninitialized -> succeeded", async () => {
  await store.dispatch(allResolved());
  use((item) => {
    expect(item.state).toBe("succeeded");
    expect(item.error).toBeNull();
    expect(item.content).toEqual(defaultItem);
  });
});

it("item uninitialized -> failed", async () => {
  await store.dispatch(allRejected());
  use((item) => {
    expect(item.state).toBe("failed");
    expect(item.error).not.toBeNull();
    expect(item.content).toBeNull();
  });
});

it("item uninitialized -> dirty", () => {
  store.dispatch(dirty());
  use((item) => {
    expect(item.state).toBe("uninitialized");
    expect(item.error).toBeNull();
    expect(item.content).toBeNull();
  });
});

it("item succeeded -> failed", async () => {
  await store.dispatch(allResolved());
  await store.dispatch(allRejected());
  use((item) => {
    expect(item.state).toBe("failed");
    expect(item.error).not.toBeNull();
    expect(item.content).toEqual(defaultItem);
  });
});

it("item failed -> succeeded", async () => {
  await store.dispatch(allRejected());
  await store.dispatch(allResolved());
  use((item) => {
    expect(item.state).toBe("succeeded");
    expect(item.error).toBeNull();
    expect(item.content).toEqual(defaultItem);
  });
});

it("item succeeded -> dirty", async () => {
  await store.dispatch(allResolved());
  store.dispatch(dirty());
  use((item) => {
    expect(item.state).toBe("dirty");
    expect(item.error).toBeNull();
    expect(item.content).toEqual(defaultItem);
  });
});

it("item failed -> dirty", async () => {
  await store.dispatch(allRejected());
  store.dispatch(dirty());
  use((item) => {
    expect(item.state).toBe("dirty");
    expect(item.error).not.toBeNull();
    expect(item.content).toBeNull();
  });
});

it("item dirty -> failed", async () => {
  await store.dispatch(allResolved());
  store.dispatch(dirty());
  await store.dispatch(allRejected());
  use((item) => {
    expect(item.state).toBe("failed");
    expect(item.error).not.toBeNull();
    expect(item.content).toEqual(defaultItem);
  });
});

it("item dirty -> succeeded", async () => {
  await store.dispatch(allResolved());
  store.dispatch(dirty());
  await store.dispatch(allResolved());
  use((item) => {
    expect(item.state).toBe("succeeded");
    expect(item.error).toBeNull();
    expect(item.content).toEqual(defaultItem);
  });
});
