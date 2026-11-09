import { useEffect, useRef, useState } from "react";
import type { FormEvent } from "react";
import { Camera, X, Save, Pencil, Trash2 } from "lucide-react";
import {
  dateLabel,
  emptyProperty,
  normalize,
  numberLabel,
  request,
  ZoneBadge,
} from "./propertyTypes";
import type { Options, Property, PropertyData } from "./propertyTypes";

type Props = {
  item: Property | null;
  options: Options;
  onClose: () => void;
  onSaved: () => void;
  onDeleted: () => void;
};
const labels: Record<keyof PropertyData, string> = {
  address: "Adresse",
  city: "Ville",
  surface: "Surface (m²)",
  dpe: "Classe DPE",
  energy: "Consommation (kWh/m²/an)",
  ges: "Classe GES",
  emissions: "Émissions (kg CO₂e/m²/an)",
  source: "Source",
  agency: "Nom de l’agence",
  notes: "Notes",
  status: "Statut",
  next_action: "Prochaine action",
  photo_id: "Photo",
};
function toData(item: Property | null): PropertyData {
  return Object.fromEntries(
    Object.keys(emptyProperty).map((key) => [
      key,
      item
        ? item[key as keyof PropertyData]
        : emptyProperty[key as keyof PropertyData],
    ]),
  ) as PropertyData;
}
export function PropertyForm({
  item,
  options,
  onClose,
  onSaved,
  onDeleted,
}: Props) {
  const [data, setData] = useState<PropertyData>(() => toData(item));
  const [editing, setEditing] = useState(!item);
  const [citySearch, setCitySearch] = useState("");
  const [otherCity, setOtherCity] = useState(
    !!item?.city && !options.cities.includes(item.city),
  );
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(
    item?.photo_url || null,
  );
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const dialog = useRef<HTMLDialogElement>(null);
  const fileInput = useRef<HTMLInputElement>(null);
  const dirty = JSON.stringify(data) !== JSON.stringify(toData(item)) || !!file;
  useEffect(() => {
    dialog.current?.showModal();
  }, []);
  useEffect(() => {
    if (!file) return;
    const url = URL.createObjectURL(file);
    setPreview(url);
    return () => URL.revokeObjectURL(url);
  }, [file]);
  useEffect(() => {
    const prevent = (event: BeforeUnloadEvent) => {
      if (dirty) {
        event.preventDefault();
        event.returnValue = "";
      }
    };
    window.addEventListener("beforeunload", prevent);
    return () => window.removeEventListener("beforeunload", prevent);
  }, [dirty]);
  const close = () => {
    if (
      !busy &&
      (!dirty ||
        window.confirm("Abandonner les modifications non enregistrées ?"))
    )
      onClose();
  };
  const set = <K extends keyof PropertyData>(key: K, value: PropertyData[K]) =>
    setData((previous) => ({ ...previous, [key]: value }));
  const zone =
    options.zones.find((z) =>
      z.cities?.some((city) => normalize(city) === normalize(data.city || "")),
    ) || options.zones.find((z) => z.id === 0)!;
  const cities = options.cities.filter(
    (city) =>
      normalize(city).includes(normalize(citySearch)) || city === data.city,
  );
  const upload = (selected: File | null) => {
    setError("");
    if (!selected) return;
    if (!["image/jpeg", "image/png"].includes(selected.type)) {
      setError("Choisissez une photo JPEG ou PNG.");
      return;
    }
    if (selected.size > 5 * 1024 * 1024) {
      setError("La photo ne doit pas dépasser 5 Mo.");
      return;
    }
    setFile(selected);
  };
  const save = async (event: FormEvent) => {
    event.preventDefault();
    if (
      item &&
      !window.confirm("Enregistrer les modifications de cette fiche ?")
    )
      return;
    setBusy(true);
    setError("");
    try {
      let photoId = data.photo_id;
      if (file) {
        const photo = await request<{ id: string }>("/api/photos", {
          method: "POST",
          headers: { "Content-Type": file.type },
          body: file,
        });
        photoId = photo.id;
        setData((previous) => ({ ...previous, photo_id: photo.id }));
        setFile(null);
        setPreview("/api/photos/" + photo.id);
      }
      await request<Property>("/api/properties" + (item ? "/" + item.id : ""), {
        method: item ? "PUT" : "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ...data,
          photo_id: photoId,
          agency: data.source === "Agence immobilière" ? data.agency : null,
          ...(item ? { version: item.version } : {}),
        }),
      });
      onSaved();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Enregistrement impossible.");
    } finally {
      setBusy(false);
    }
  };
  const remove = async () => {
    if (
      !item ||
      !window.confirm(
        "Supprimer ce bien de la liste ? Son historique et ses photos seront conservés localement.",
      )
    )
      return;
    setBusy(true);
    setError("");
    try {
      await request(
        "/api/properties/" + item.id + "?confirm=true&version=" + item.version,
        { method: "DELETE" },
      );
      onDeleted();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Suppression impossible.");
    } finally {
      setBusy(false);
    }
  };
  const textField = (key: "address" | "agency", max: number) => (
    <label className={key === "address" ? "span-2" : ""}>
      {labels[key]}
      <input
        maxLength={max}
        value={data[key] || ""}
        onChange={(e) => set(key, e.target.value || null)}
      />
    </label>
  );
  const numericField = (key: "surface" | "energy" | "emissions") => (
    <label>
      {labels[key]}
      <input
        type="number"
        min="0"
        max="1000000000"
        step="any"
        value={data[key] ?? ""}
        onChange={(e) =>
          set(key, e.target.value === "" ? null : Number(e.target.value))
        }
      />
    </label>
  );
  const letterField = (key: "dpe" | "ges") => (
    <label>
      {labels[key]}
      <select
        aria-label={labels[key]}
        value={data[key] || ""}
        onChange={(e) => set(key, e.target.value || null)}
      >
        <option value="">Non renseigné</option>
        {"ABCDEFG".split("").map((v) => (
          <option key={v}>{v}</option>
        ))}
      </select>
    </label>
  );
  return (
    <dialog
      ref={dialog}
      className="property-dialog"
      aria-labelledby="property-dialog-title"
      onCancel={(e) => {
        e.preventDefault();
        close();
      }}
    >
      <div className="dialog-heading">
        <div>
          <p className="eyebrow">VOTRE PORTEFEUILLE</p>
          <h2 id="property-dialog-title">
            {item
              ? editing
                ? "Modifier le bien"
                : "Fiche du bien"
              : "Ajouter un bien"}
          </h2>
        </div>
        <button
          className="icon-button"
          type="button"
          onClick={close}
          aria-label="Fermer la fiche"
          disabled={busy}
        >
          <X size={20} />
        </button>
      </div>
      {error && (
        <p className="error-message" role="alert">
          {error}
        </p>
      )}
      {editing ? (
        <form onSubmit={save}>
          <fieldset disabled={busy} className="form-body">
            <p className="muted">
              Tous les renseignements peuvent rester vides. N’enregistrez aucune
              coordonnée de propriétaire, y compris dans les notes.
            </p>
            <section className="photo-field">
              <div className="photo-preview">
                {preview ? (
                  <img src={preview} alt="Photo du bien" />
                ) : (
                  <Camera size={32} strokeWidth={1} />
                )}
              </div>
              <div>
                <h3>Photo du bien</h3>
                <p className="muted">
                  JPEG ou PNG · 5 Mo maximum · conservée sur cet ordinateur
                </p>
                <label className="file-label">
                  Choisir une photo
                  <input
                    ref={fileInput}
                    className="sr-only"
                    type="file"
                    accept="image/jpeg,image/png"
                    onChange={(e) => upload(e.target.files?.[0] || null)}
                  />
                </label>
                {(preview || file) && (
                  <button
                    className="text-button danger"
                    type="button"
                    onClick={() => {
                      setFile(null);
                      setPreview(null);
                      set("photo_id", null);
                      if (fileInput.current) fileInput.current.value = "";
                    }}
                  >
                    Retirer la photo
                  </button>
                )}
              </div>
            </section>
            <h3 className="form-section-title">Localisation</h3>
            <div className="form-grid">
              {textField("address", 500)}
              <label>
                Rechercher une commune
                <input
                  type="search"
                  value={citySearch}
                  placeholder="Nom de la commune…"
                  onChange={(e) => setCitySearch(e.target.value)}
                />
              </label>
              <label>
                Ville
                <select
                  aria-label="Ville"
                  value={otherCity ? "__other" : data.city || ""}
                  onChange={(e) => {
                    setOtherCity(e.target.value === "__other");
                    set(
                      "city",
                      e.target.value === "__other"
                        ? null
                        : e.target.value || null,
                    );
                  }}
                >
                  <option value="">Non renseignée</option>
                  {cities.map((city) => (
                    <option key={city}>{city}</option>
                  ))}
                  <option value="__other">Autre ville</option>
                </select>
              </label>
              {otherCity && (
                <label>
                  Autre ville
                  <input
                    maxLength={150}
                    value={data.city || ""}
                    onChange={(e) => set("city", e.target.value || null)}
                    placeholder="Saisir la ville"
                  />
                </label>
              )}
              <div className="zone-field">
                <span>Zone calculée automatiquement</span>
                <ZoneBadge zone={zone} />
              </div>
            </div>
            <h3 className="form-section-title">Caractéristiques & énergie</h3>
            <div className="form-grid">
              {numericField("surface")}
              <span />
              {letterField("dpe")}
              {numericField("energy")}
              {letterField("ges")}
              {numericField("emissions")}
            </div>
            <h3 className="form-section-title">Origine & suivi</h3>
            <div className="form-grid">
              <label>
                Source
                <select
                  aria-label="Source"
                  value={data.source || ""}
                  onChange={(e) =>
                    setData((previous) => ({
                      ...previous,
                      source: e.target.value || null,
                      agency:
                        e.target.value === "Agence immobilière"
                          ? previous.agency
                          : null,
                    }))
                  }
                >
                  <option value="">Non renseignée</option>
                  <option>Registre DPE</option>
                  <option>Agence immobilière</option>
                </select>
              </label>
              {data.source === "Agence immobilière" && textField("agency", 200)}
              <label>
                Statut
                <select
                  aria-label="Statut"
                  value={data.status}
                  onChange={(e) => set("status", e.target.value)}
                >
                  {options.statuses.map((status) => (
                    <option key={status}>{status}</option>
                  ))}
                </select>
              </label>
              <label>
                Date de prochaine action
                <input
                  type="date"
                  value={data.next_action || ""}
                  onChange={(e) => set("next_action", e.target.value || null)}
                />
              </label>
              <label className="span-2">
                Notes
                <textarea
                  rows={4}
                  maxLength={10000}
                  value={data.notes || ""}
                  onChange={(e) => set("notes", e.target.value || null)}
                />
              </label>
            </div>
            {item && (
              <p className="muted">
                Créé le {dateLabel(item.created_at, true)} · Dernière
                modification le {dateLabel(item.updated_at, true)}
              </p>
            )}
          </fieldset>
          <div className="dialog-actions">
            <button
              type="button"
              className="secondary-button"
              disabled={busy}
              onClick={close}
            >
              Annuler
            </button>
            <button className="primary-button" type="submit" disabled={busy}>
              <Save size={16} />
              {busy ? "Enregistrement…" : "Enregistrer"}
            </button>
          </div>
        </form>
      ) : (
        item && (
          <>
            <div className="form-body">
              <div className="detail-intro">
                {item.photo_url ? (
                  <img
                    className="detail-photo"
                    src={item.photo_url}
                    alt="Photo du bien"
                  />
                ) : (
                  <div className="detail-photo no-photo">
                    <Camera size={36} />
                    <span>Aucune photo</span>
                  </div>
                )}
                <div>
                  <ZoneBadge zone={item.zone} />
                  <h3>{item.address || "Adresse non renseignée"}</h3>
                  <p>{item.city || "Ville non renseignée"}</p>
                  <span
                    className={
                      "status-badge status-" +
                      options.statuses.indexOf(item.status)
                    }
                  >
                    {item.status}
                  </span>
                </div>
              </div>
              <dl className="property-details">
                {(Object.keys(labels) as (keyof PropertyData)[])
                  .filter(
                    (key) => !["photo_id", "address", "city"].includes(key),
                  )
                  .map((key) => (
                    <div key={key}>
                      <dt>{labels[key]}</dt>
                      <dd>
                        {key === "next_action"
                          ? dateLabel(item.next_action)
                          : typeof item[key] === "number"
                            ? numberLabel(item[key] as number)
                            : item[key] || "—"}
                      </dd>
                    </div>
                  ))}
                <div>
                  <dt>Identifiant interne</dt>
                  <dd className="internal-id">{item.id}</dd>
                </div>
                <div>
                  <dt>Création</dt>
                  <dd>{dateLabel(item.created_at, true)}</dd>
                </div>
                <div>
                  <dt>Dernière modification</dt>
                  <dd>{dateLabel(item.updated_at, true)}</dd>
                </div>
              </dl>
              <h3 className="form-section-title">Historique des actions</h3>
              <div className="property-history">
                {item.history?.map((entry, index) => (
                  <details key={index}>
                    <summary>
                      {entry.action} · {dateLabel(entry.occurred_at, true)}
                    </summary>
                    <dl className="property-details">
                      {(Object.keys(labels) as (keyof PropertyData)[])
                        .filter((key) => key !== "photo_id")
                        .map((key) => (
                          <div key={key}>
                            <dt>{labels[key]}</dt>
                            <dd>{String(entry.snapshot[key] ?? "—")}</dd>
                          </div>
                        ))}
                      {entry.snapshot.photo_url && (
                        <a
                          href={entry.snapshot.photo_url}
                          target="_blank"
                          rel="noreferrer"
                        >
                          Voir la photo de cette version
                        </a>
                      )}
                    </dl>
                  </details>
                ))}
              </div>
            </div>
            <div className="dialog-actions">
              <button
                className="text-button danger"
                type="button"
                disabled={busy}
                onClick={remove}
              >
                <Trash2 size={16} /> Supprimer
              </button>
              <button
                className="primary-button"
                type="button"
                onClick={() => setEditing(true)}
              >
                <Pencil size={16} /> Modifier la fiche
              </button>
            </div>
          </>
        )
      )}
    </dialog>
  );
}
