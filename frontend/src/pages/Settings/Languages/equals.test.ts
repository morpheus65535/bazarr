import {
  encodeEqualData,
  LanguageEqualData,
  LanguageEqualImmediateData,
  parseEqualData,
} from "@/pages/Settings/Languages/equals";
import { describe, expect, it } from "vitest";

describe("Equals Parser", () => {
  it("should parse from string correctly", () => {
    interface TestData {
      text: string;
      expected: LanguageEqualImmediateData;
    }

    function testParsedResult(
      text: string,
      expected: LanguageEqualImmediateData
    ) {
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

  it("should encode to string correctly", () => {
    interface TestData {
      source: LanguageEqualData;
      expected: string;
    }

    const testValues: TestData[] = [
      {
        source: {
          source: {
            name: "Abkhazian",
            code2: "ab",
            code3: "abk",
            enabled: false,
          },
          hi: false,
          forced: false,
          target: {
            name: "Aragonese",
            code2: "an",
            code3: "arg",
            enabled: false,
          },
        },
        expected: "abk:arg",
      },
      {
        source: {
          source: {
            name: "Abkhazian",
            code2: "ab",
            code3: "abk",
            enabled: false,
          },
          hi: true,
          forced: false,
          target: {
            name: "Aragonese",
            code2: "an",
            code3: "arg",
            enabled: false,
          },
        },
        expected: "abk@hi:arg",
      },
      {
        source: {
          source: {
            name: "Abkhazian",
            code2: "ab",
            code3: "abk",
            enabled: false,
          },
          hi: false,
          forced: true,
          target: {
            name: "Aragonese",
            code2: "an",
            code3: "arg",
            enabled: false,
          },
        },
        expected: "abk@forced:arg",
      },
    ];

    function testEncodeResult({ source, expected }: TestData) {
      const encoded = encodeEqualData(source);

      expect(
        encoded,
        `Encoded result '${encoded}' is not matched to '${expected}'`
      ).toEqual(expected);
    }

    testValues.forEach(testEncodeResult);
  });
});
