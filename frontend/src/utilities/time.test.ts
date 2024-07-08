import {
  divisorDay,
  divisorHour,
  divisorMinute,
  divisorSecond,
  formatTime,
} from "./time";

describe("formatTime", () => {
  it("should format day hour minute and second", () => {
    const uptimeInSeconds = 3661;

    const formattedTime = formatTime(uptimeInSeconds, [
      { unit: "d", divisor: divisorDay },
      { unit: "h", divisor: divisorHour },
      { unit: "m", divisor: divisorMinute },
      { unit: "s", divisor: divisorSecond },
    ]);

    expect(formattedTime).toBe("0d 01:01:01");
  });

  it("should format multiple digits of days", () => {
    const uptimeInSeconds = 50203661;

    const formattedTime = formatTime(uptimeInSeconds, [
      { unit: "d", divisor: divisorDay },
      { unit: "h", divisor: divisorHour },
      { unit: "m", divisor: divisorMinute },
      { unit: "s", divisor: divisorSecond },
    ]);

    expect(formattedTime).toBe("581d 01:27:41");
  });

  it("should format time day hour minute", () => {
    const uptimeInSeconds = 3661;

    const formattedTime = formatTime(uptimeInSeconds, [
      { unit: "d", divisor: divisorDay },
      { unit: "h", divisor: divisorHour },
      { unit: "m", divisor: divisorMinute },
    ]);

    expect(formattedTime).toBe("0d 01:01");
  });

  it("should format zero uptime", () => {
    const uptimeInSeconds = 0;

    const formattedTime = formatTime(uptimeInSeconds, [
      { unit: "d", divisor: divisorDay },
      { unit: "h", divisor: divisorHour },
      { unit: "m", divisor: divisorMinute },
      { unit: "s", divisor: divisorSecond },
    ]);

    expect(formattedTime).toBe("0d 00:00:00");
  });
});
