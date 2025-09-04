export type Locale = "zh" | "fr";

export async function getDictionary(locale: Locale): Promise<Record<string, string>> {
  switch (locale) {
    case "fr":
      return (await import("@/dictionaries/fr.json")).default as Record<string, string>;
    case "zh":
    default:
      return (await import("@/dictionaries/zh.json")).default as Record<string, string>;
  }
}

