import {} from "jest";
import { AsyncUtility } from "../async";

interface AsyncTest {
  id: string;
  name: string;
}

it("Item Init", () => {
  const item = AsyncUtility.getDefaultItem<AsyncTest>();
  expect(item.state).toEqual("uninitialized");
  expect(item.error).toBeNull();
  expect(item.content).toBeNull();
});

it("List Init", () => {
  const list = AsyncUtility.getDefaultList<AsyncTest>();
  expect(list.state).toEqual("uninitialized");
  expect(list.dirtyEntities).toHaveLength(0);
  expect(list.error).toBeNull();
  expect(list.content).toHaveLength(0);
});

it("Entity Init", () => {
  const entity = AsyncUtility.getDefaultEntity<AsyncTest>("id");
  expect(entity.state).toEqual("uninitialized");
  expect(entity.dirtyEntities).toHaveLength(0);
  expect(entity.error).toBeNull();
  expect(entity.content.ids).toHaveLength(0);
  expect(entity.content.keyName).toBe("id");
  expect(entity.content.entities).toMatchObject({});
});
