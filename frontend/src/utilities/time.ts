interface TimeFormat {
  unit: string;
  divisor: number;
}

export const divisorDay = 24 * 60 * 60;
export const divisorHour = 60 * 60;
export const divisorMinute = 60;
export const divisorSecond = 1;

export const formatTime = (
  uptimeInSeconds: number,
  formats: TimeFormat[],
): string =>
  formats.reduce(
    (formattedTime: string, { unit, divisor }: TimeFormat, index: number) => {
      const timeValue: number =
        index === 0
          ? Math.floor(uptimeInSeconds / divisor)
          : Math.floor(uptimeInSeconds / divisor) % 60;
      return (
        formattedTime +
        (index === 0
          ? `${timeValue}${unit} `
          : `${timeValue.toString().padStart(2, "0")}${index < formats.length - 1 ? ":" : ""}`)
      );
    },
    "",
  );
