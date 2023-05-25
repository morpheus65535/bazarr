import {
  LanguageEqualImmediateData,
  parseEqualData,
} from "@/pages/Settings/Languages";
import { describe, expect, it } from "vitest";

function testParsedResult(text: string, expected: LanguageEqualImmediateData) {
  const result = parseEqualData(text);

  if (result === undefined) {
    expect(false, `Cannot parse '${text}' as language equal data`);
    return;
  }

  expect(
    result,
    `${text} does not match with the expected equal data`
  ).toStrictEqual(expected);
}

interface TestData {
  text: string;
  expected: LanguageEqualImmediateData;
}

describe("Equals Parser", () => {
  it("should parse string correctly", () => {
    const testValues: TestData[] = [
      {
        text: "spa-MX:spa",
        expected: {
          source: "spa-MX",
          hi: false,
          forced: false,
          target: "spa",
        },
      },
      {
        text: "zho@hi:zht",
        expected: {
          source: "zho",
          hi: true,
          forced: false,
          target: "zht",
        },
      },
      {
        text: "es-MX@forced:es-MX",
        expected: {
          source: "es-MX",
          hi: false,
          forced: true,
          target: "es-MX",
        },
      },
      {
        text: "en@hi:en",
        expected: {
          source: "en",
          hi: true,
          forced: false,
          target: "en",
        },
      },
    ];

    testValues.forEach((data) => {
      testParsedResult(data.text, data.expected);
    });
  });
});
