export const statuses = [
  "Non prospecté",
  "Prospection prévue",
  "Prospection impossible",
  "Prospecté",
] as const;
export type Zone = {
  id: number;
  name: string;
  color: string;
  cities?: string[];
};
export type PropertyData = {
  address: string | null;
  city: string | null;
  surface: number | null;
  dpe: string | null;
  energy: number | null;
  ges: string | null;
  emissions: number | null;
  source: string | null;
  agency: string | null;
  notes: string | null;
  status: string;
  next_action: string | null;
  photo_id: string | null;
};
export type Property = PropertyData & {
  id: string;
  version: number;
  created_at: string;
  updated_at: string;
  zone: Zone;
  photo_url: string | null;
  history?: HistoryEntry[];
};
export type HistoryEntry = {
  action: string;
  occurred_at: string;
  snapshot: Property;
};
export type Options = { cities: string[]; zones: Zone[]; statuses: string[] };
export type PropertyList = {
  items: Property[];
  total: number;
  page: number;
  pages: number;
};
export const emptyProperty: PropertyData = {
  address: null,
  city: null,
  surface: null,
  dpe: null,
  energy: null,
  ges: null,
  emissions: null,
  source: null,
  agency: null,
  notes: null,
  status: "Non prospecté",
  next_action: null,
  photo_id: null,
};
export const normalize = (text: string) =>
  text
    .normalize("NFKD")
    .replace(/\p{M}/gu, "")
    .toLocaleLowerCase("fr")
    .trim()
    .replace(/\s+/g, " ");
export const dateLabel = (date: string | null, withTime = false) =>
  date
    ? new Date(date.length === 10 ? date + "T12:00:00" : date).toLocaleString(
        "fr-FR",
        withTime
          ? { dateStyle: "short", timeStyle: "short" }
          : { dateStyle: "short" },
      )
    : "—";
export const numberLabel = (value: number | null) =>
  value === null ? "—" : value.toLocaleString("fr-FR");
export function ZoneBadge({ zone }: { zone: Zone }) {
  return (
    <span
      className="zone-badge"
      style={{
        color: zone.color,
        background: zone.color + "12",
        borderColor: zone.color + "35",
      }}
    >
      <span style={{ background: zone.color }} />
      {zone.name}
    </span>
  );
}
export async function request<T>(url: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(url, init);
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError")
      throw error;
    throw new Error(
      "Connexion au serveur local impossible. Vérifiez son démarrage puis réessayez.",
    );
  }
  if (!response.ok) {
    let message = "Le serveur local est indisponible. Vérifiez son démarrage.";
    try {
      const body = await response.json();
      if (typeof body.detail === "string") message = body.detail;
    } catch {
      /* Use the readable fallback. */
    }
    throw new Error(message);
  }
  return response.json();
}
