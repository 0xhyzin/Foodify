const formatter = new Intl.NumberFormat("ar-EG", {
  style: "currency",
  currency: "EGP",
  maximumFractionDigits: 2,
});
export const formatMoney = (value: string) => formatter.format(Number(value));
export function minorUnits(value: string): number {
  if (!/^\d{1,10}(\.\d{1,2})?$/.test(value))
    throw new Error("Invalid monetary amount");
  const [whole, cents = ""] = value.split(".");
  return Number(whole) * 100 + Number(cents.padEnd(2, "0"));
}
export const fromMinor = (value: number): string =>
  `${Math.floor(value / 100)}.${String(value % 100).padStart(2, "0")}`;
