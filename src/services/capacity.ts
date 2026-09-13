export function formatCapacity(value: { used: number; total: number; usedBytes?: number; totalBytes?: number }, legacyPower: number): string {
  const total = value.totalBytes ?? value.total * 1024 ** legacyPower
  const used = value.usedBytes ?? value.used * 1024 ** legacyPower
  const power = total >= 1024 ** 4 ? 4 : 3
  const format = (bytes: number) => Number((bytes / 1024 ** power).toFixed(2)).toString()
  return `${format(used)} / ${format(total)} ${power === 4 ? 'TiB' : 'GiB'}`
}
