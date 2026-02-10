export type PlainObject = Record<string, any>;

const isPlainObject = (value: unknown): value is PlainObject =>
  typeof value === 'object' && value !== null && !Array.isArray(value);

export function deepMerge<T extends PlainObject>(base: T, patch: PlainObject): T {
  const output: PlainObject = { ...base };
  Object.entries(patch || {}).forEach(([key, value]) => {
    if (Array.isArray(value)) {
      output[key] = [...value];
      return;
    }
    if (isPlainObject(value) && isPlainObject(output[key])) {
      output[key] = deepMerge(output[key] as PlainObject, value);
      return;
    }
    output[key] = value;
  });
  return output as T;
}
