const currencyFormatter = new Intl.NumberFormat('ar-EG', { style: 'currency', currency: 'EGP', maximumFractionDigits: 0 });
const numberFormatter = new Intl.NumberFormat('ar-EG', { maximumFractionDigits: 1 });

export const formatPrice = (price: number): string => currencyFormatter.format(price);
export const formatNumber = (number: number): string => numberFormatter.format(number);
