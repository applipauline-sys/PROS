import { useEffect, useRef, useState } from "react";
import {
  Plus,
  Search,
  SlidersHorizontal,
  Camera,
  ChevronLeft,
  ChevronRight,
  RotateCcw,
} from "lucide-react";
import { PropertyForm } from "./PropertyForm";
import { dateLabel, numberLabel, request, ZoneBadge } from "./propertyTypes";
import type { Options, Property, PropertyList } from "./propertyTypes";

const defaults = {
  q: "",
  city: "",
  zone: "",
  source: "",
  status: "",
  sort: "created_at",
  direction: "desc",
  page: 1,
  page_size: 25,
};
export function Properties() {
  const [options, setOptions] = useState<Options | null>(null);
  const [filters, setFilters] = useState(defaults);
  const [query, setQuery] = useState("");
  const [result, setResult] = useState<PropertyList | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [showFilters, setShowFilters] = useState(false);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [form, setForm] = useState<Property | "new" | null>(null);
  const [refresh, setRefresh] = useState(0);
  const [opening, setOpening] = useState(false);
  const selectAll = useRef<HTMLInputElement>(null);
  const opener = useRef<HTMLElement | null>(null);
  useEffect(() => {
    const timer = setTimeout(
      () => setFilters((old) => ({ ...old, q: query, page: 1 })),
      250,
    );
    return () => clearTimeout(timer);
  }, [query]);
  useEffect(() => {
    request<Options>("/api/property-options")
      .then(setOptions)
      .catch(() =>
        setError(
          "Impossible de charger les communes. Vérifiez le serveur puis réessayez.",
        ),
      );
  }, [refresh]);
  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setError("");
    const params = new URLSearchParams();
    Object.entries(filters).forEach(([key, value]) => {
      if (value !== "") params.set(key, String(value));
    });
    request<PropertyList>("/api/properties?" + params, {
      signal: controller.signal,
    })
      .then((data) => {
        if (!controller.signal.aborted) setResult(data);
      })
      .catch((e) => {
        if (!controller.signal.aborted)
          setError(e instanceof Error ? e.message : "Chargement impossible.");
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [filters, refresh]);
  useEffect(() => {
    if (selectAll.current)
      selectAll.current.indeterminate =
        !!result?.items.some((item) => selected.has(item.id)) &&
        !result?.items.every((item) => selected.has(item.id));
  }, [result, selected]);
  const change = (key: keyof typeof defaults, value: string | number) => {
    setFilters((old) => ({ ...old, [key]: value, page: 1 }));
    setSelected(new Set());
  };
  const reset = () => {
    setQuery("");
    setFilters(defaults);
    setSelected(new Set());
  };
  const close = () => {
    setForm(null);
    setTimeout(() => opener.current?.focus(), 0);
  };
  const saved = (deleted = false) => {
    close();
    setRefresh((n) => n + 1);
    setSelected(new Set());
    setNotice(
      deleted
        ? "Bien supprimé de la liste. Son historique est conservé localement."
        : "Fiche enregistrée sur cet ordinateur.",
    );
  };
  const open = async (item: Property) => {
    if (opening) return;
    opener.current = document.activeElement as HTMLElement;
    setOpening(true);
    setError("");
    try {
      setForm(await request<Property>("/api/properties/" + item.id));
    } catch (e) {
      setError(
        e instanceof Error ? e.message : "Impossible d’ouvrir la fiche.",
      );
    } finally {
      setOpening(false);
    }
  };
  const activeFilters = ["city", "zone", "source", "status"].filter(
    (key) => filters[key as keyof typeof filters] !== "",
  ).length;
  return (
    <section className="properties-module" aria-label="Gestion des biens">
      <div className="properties-toolbar">
        <div className="search-box">
          <Search size={17} />
          <input
            aria-label="Rechercher un bien"
            type="search"
            placeholder="Adresse, ville, source ou agence…"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
        </div>
        <button
          className="secondary-button"
          aria-expanded={showFilters}
          aria-controls="property-filters"
          onClick={() => setShowFilters(!showFilters)}
        >
          <SlidersHorizontal size={16} /> Filtres
          {activeFilters > 0 && (
            <span className="filter-count">{activeFilters}</span>
          )}
        </button>
        <button
          className="primary-button"
          disabled={!options}
          onClick={() => {
            opener.current = document.activeElement as HTMLElement;
            setForm("new");
            setNotice("");
          }}
        >
          <Plus size={17} /> Ajouter un bien
        </button>
      </div>
      {showFilters && (
        <div id="property-filters" className="filter-grid">
          <label>
            Ville exacte
            <input
              value={filters.city}
              placeholder="Toutes les villes"
              onChange={(e) => change("city", e.target.value)}
            />
          </label>
          <label>
            Zone
            <select
              aria-label="Zone"
              value={filters.zone}
              onChange={(e) => change("zone", e.target.value)}
            >
              <option value="">Toutes les zones</option>
              {options?.zones.map((z) => (
                <option value={z.id} key={z.id}>
                  {z.name}
                </option>
              ))}
            </select>
          </label>
          <label>
            Source
            <select
              aria-label="Source"
              value={filters.source}
              onChange={(e) => change("source", e.target.value)}
            >
              <option value="">Toutes les sources</option>
              <option>Registre DPE</option>
              <option>Agence immobilière</option>
            </select>
          </label>
          <label>
            Statut
            <select
              aria-label="Statut"
              value={filters.status}
              onChange={(e) => change("status", e.target.value)}
            >
              <option value="">Tous les statuts</option>
              {options?.statuses.map((s) => <option key={s}>{s}</option>)}
            </select>
          </label>
          <button className="text-button" onClick={reset}>
            <RotateCcw size={14} /> Réinitialiser
          </button>
        </div>
      )}
      {notice && (
        <div className="success-message" role="status">
          {notice}
          <button
            className="text-button"
            aria-label="Masquer le message"
            onClick={() => setNotice("")}
          >
            ×
          </button>
        </div>
      )}
      {error && (
        <div className="error-message" role="alert">
          {error}{" "}
          <button
            className="text-button"
            onClick={() => setRefresh((n) => n + 1)}
          >
            Réessayer
          </button>
        </div>
      )}
      <div className="list-controls">
        <span role="status">
          {loading
            ? "Chargement…"
            : `${result?.total ?? 0} bien${result?.total === 1 ? "" : "s"}`}
          {selected.size > 0 &&
            ` · ${selected.size} sélectionné${selected.size > 1 ? "s" : ""}`}
          {opening && " · Ouverture…"}
        </span>
        <div>
          <label>
            Trier par
            <select
              value={filters.sort}
              onChange={(e) => change("sort", e.target.value)}
            >
              <option value="city">Ville</option>
              <option value="zone">Zone</option>
              <option value="created_at">Date de création</option>
              <option value="updated_at">Dernière modification</option>
              <option value="next_action">Prochaine action</option>
              <option value="status">Statut</option>
            </select>
          </label>
          <label>
            <span className="sr-only">Sens du tri</span>
            <select
              value={filters.direction}
              onChange={(e) => change("direction", e.target.value)}
            >
              <option value="asc">Croissant</option>
              <option value="desc">Décroissant</option>
            </select>
          </label>
        </div>
      </div>
      <div
        className="table-scroll"
        aria-busy={loading}
        tabIndex={0}
        role="region"
        aria-label="Tableau des biens, défilement horizontal disponible"
      >
        <table className="property-table">
          <caption className="sr-only">
            Biens immobiliers correspondant à la recherche
          </caption>
          <thead>
            <tr>
              <th>
                <input
                  ref={selectAll}
                  type="checkbox"
                  aria-label="Sélectionner les biens de cette page"
                  disabled={loading || !result?.items.length}
                  checked={
                    !!result?.items.length &&
                    result.items.every((item) => selected.has(item.id))
                  }
                  onChange={(e) =>
                    setSelected((previous) => {
                      const next = new Set(previous);
                      result?.items.forEach((item) =>
                        e.target.checked
                          ? next.add(item.id)
                          : next.delete(item.id),
                      );
                      return next;
                    })
                  }
                />
              </th>
              <th>Photo</th>
              <th>Adresse</th>
              <th>Ville</th>
              <th>Zone</th>
              <th>Surface</th>
              <th>DPE</th>
              <th>GES</th>
              <th>Source</th>
              <th>Statut</th>
              <th>Prochaine action</th>
            </tr>
          </thead>
          <tbody>
            {!loading &&
              !error &&
              result?.items.map((item) => (
                <tr
                  key={item.id}
                  onClick={(e) => {
                    if (!(e.target as HTMLElement).closest("button,input,a"))
                      void open(item);
                  }}
                >
                  <td>
                    <input
                      type="checkbox"
                      aria-label={"Sélectionner " + (item.address || item.id)}
                      checked={selected.has(item.id)}
                      onChange={(e) =>
                        setSelected((previous) => {
                          const next = new Set(previous);
                          e.target.checked
                            ? next.add(item.id)
                            : next.delete(item.id);
                          return next;
                        })
                      }
                    />
                  </td>
                  <td>
                    {item.photo_url ? (
                      <img
                        className="table-photo"
                        src={item.photo_url}
                        loading="lazy"
                        alt={"Photo — " + (item.address || "bien")}
                      />
                    ) : (
                      <span className="table-photo no-photo">
                        <Camera size={17} />
                      </span>
                    )}
                  </td>
                  <td>
                    <button
                      className="property-address"
                      onClick={() => void open(item)}
                      disabled={opening}
                    >
                      {item.address || "Adresse à compléter"}
                    </button>
                  </td>
                  <td>{item.city || "—"}</td>
                  <td>
                    <ZoneBadge zone={item.zone} />
                  </td>
                  <td className="numeric">
                    {numberLabel(item.surface)}
                    {item.surface !== null ? " m²" : ""}
                  </td>
                  <td>
                    {item.dpe ? (
                      <span className={"energy-badge energy-" + item.dpe}>
                        {item.dpe}
                      </span>
                    ) : (
                      "—"
                    )}
                  </td>
                  <td>
                    {item.ges ? (
                      <span className="ges-badge">{item.ges}</span>
                    ) : (
                      "—"
                    )}
                  </td>
                  <td>
                    <span>{item.source || "—"}</span>
                    {item.agency && (
                      <small className="agency-name">{item.agency}</small>
                    )}
                  </td>
                  <td>
                    <span
                      className={
                        "status-badge status-" +
                        (options?.statuses.indexOf(item.status) ?? 0)
                      }
                    >
                      {item.status}
                    </span>
                  </td>
                  <td>{dateLabel(item.next_action)}</td>
                </tr>
              ))}
          </tbody>
        </table>
        {!loading && !error && !result?.items.length && (
          <div className="list-empty">
            <Camera size={30} strokeWidth={1} />
            <h2>
              {filters.q || activeFilters
                ? "Aucun résultat"
                : "Votre portefeuille commence ici"}
            </h2>
            <p>
              {filters.q || activeFilters
                ? "Modifiez vos critères pour retrouver vos biens."
                : "Ajoutez votre premier bien. Les informations inconnues pourront être complétées plus tard."}
            </p>
            {(!!filters.q || activeFilters > 0) && (
              <button className="secondary-button" onClick={reset}>
                Effacer les critères
              </button>
            )}
          </div>
        )}
        {loading && <p className="list-loading">Chargement des biens…</p>}
      </div>
      <div className="pagination">
        <label>
          Biens par page
          <select
            value={filters.page_size}
            onChange={(e) => change("page_size", Number(e.target.value))}
          >
            {[10, 25, 50, 100].map((n) => (
              <option key={n} value={n}>
                {n}
              </option>
            ))}
          </select>
        </label>
        <div>
          <button
            className="icon-button"
            aria-label="Page précédente"
            disabled={loading || !result || result.page <= 1}
            onClick={() =>
              setFilters((old) => ({ ...old, page: (result?.page || 1) - 1 }))
            }
          >
            <ChevronLeft size={18} />
          </button>
          <span>
            Page {result?.page || 1} sur {result?.pages || 1}
          </span>
          <button
            className="icon-button"
            aria-label="Page suivante"
            disabled={loading || !result || result.page >= result.pages}
            onClick={() =>
              setFilters((old) => ({ ...old, page: (result?.page || 1) + 1 }))
            }
          >
            <ChevronRight size={18} />
          </button>
        </div>
      </div>
      {selected.size > 0 && (
        <p className="muted">
          La sélection est préparée pour les futures actions groupées. Aucune
          modification collective n’est appliquée à cette étape.
        </p>
      )}
      {form && options && (
        <PropertyForm
          item={form === "new" ? null : form}
          options={options}
          onClose={close}
          onSaved={() => saved()}
          onDeleted={() => saved(true)}
        />
      )}
    </section>
  );
}
