import { describe, expect, it } from "vitest";
import {
  decodeEqualData,
  encodeEqualData,
  LanguageEqualData,
  LanguageEqualImmediateData,
} from "@/pages/Settings/Languages/equals";

describe("Equals Parser", () => {
  it("should parse from string correctly", () => {
    interface TestData {
      text: string;
      expected: LanguageEqualImmediateData;
    }

    function testParsedResult(
      text: string,
      expected: LanguageEqualImmediateData,
    ) {
      const result = decodeEqualData(text);

      if (result === undefined) {
        expect(false, `Cannot parse '${text}' as language equal data`);
        return;
      }

      expect(
        result,
        `${text} does not match with the expected equal data`,
      ).toStrictEqual(expected);
    }

    const testValues: TestData[] = [
      {
        text: "spa-MX:spa",
        expected: {
          source: {
            content: "spa-MX",
            hi: false,
            forced: false,
          },
          target: {
            content: "spa",
            hi: false,
            forced: false,
          },
        },
      },
      {
        text: "zho@hi:zht",
        expected: {
          source: {
            content: "zho",
            hi: true,
            forced: false,
          },
          target: {
            content: "zht",
            hi: false,
            forced: false,
          },
        },
      },
      {
        text: "es-MX@forced:es-MX",
        expected: {
          source: {
            content: "es-MX",
            hi: false,
            forced: true,
          },
          target: {
            content: "es-MX",
            hi: false,
            forced: false,
          },
        },
      },
      {
        text: "en:en@hi",
        expected: {
          source: {
            content: "en",
            hi: false,
            forced: false,
          },
          target: {
            content: "en",
            hi: true,
            forced: false,
          },
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
            content: {
              name: "Abkhazian",
              code2: "ab",
              code3: "abk",
              enabled: false,
            },
            hi: false,
            forced: false,
          },
          target: {
            content: {
              name: "Aragonese",
              code2: "an",
              code3: "arg",
              enabled: false,
            },
            hi: false,
            forced: false,
          },
        },
        expected: "abk:arg",
      },
      {
        source: {
          source: {
            content: {
              name: "Abkhazian",
              code2: "ab",
              code3: "abk",
              enabled: false,
            },
            hi: true,
            forced: false,
          },
          target: {
            content: {
              name: "Aragonese",
              code2: "an",
              code3: "arg",
              enabled: false,
            },
            hi: false,
            forced: false,
          },
        },
        expected: "abk@hi:arg",
      },
      {
        source: {
          source: {
            content: {
              name: "Abkhazian",
              code2: "ab",
              code3: "abk",
              enabled: false,
            },
            hi: false,
            forced: true,
          },
          target: {
            content: {
              name: "Aragonese",
              code2: "an",
              code3: "arg",
              enabled: false,
            },
            hi: false,
            forced: false,
          },
        },
        expected: "abk@forced:arg",
      },
    ];

    function testEncodeResult({ source, expected }: TestData) {
      const encoded = encodeEqualData(source);

      expect(
        encoded,
        `Encoded result '${encoded}' is not matched to '${expected}'`,
      ).toEqual(expected);
    }

    testValues.forEach(testEncodeResult);
  });
});
