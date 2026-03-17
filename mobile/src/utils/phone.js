export function normalizeIraqiPhone(value) {
  const digits = String(value || '').replace(/\D/g, '');
  if (digits.startsWith('00964') && digits.length >= 14) return `0${digits.slice(5, 15)}`.slice(0, 11);
  if (digits.startsWith('964') && digits.length >= 13) return `0${digits.slice(3, 13)}`.slice(0, 11);
  if (digits.startsWith('7') && digits.length >= 10) return `0${digits.slice(0, 10)}`;
  return digits.slice(0, 11);
}

export function isValidIraqiPhone(value) {
  return /^07\d{9}$/.test(String(value || ''));
}
