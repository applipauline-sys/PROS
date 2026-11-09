import { useEffect, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { LayoutDashboard, House, CalendarDays, MapPin, ChartNoAxesCombined, Settings, ArrowUpRight, ShieldCheck, Circle, Building2 } from 'lucide-react';
import './style.css';

const pages = [
  { id: 'tableau-de-bord', title: 'Tableau de bord', icon: LayoutDashboard, subtitle: 'Une vision claire de votre prospection.' },
  { id: 'mes-biens', title: 'Mes biens', icon: House, subtitle: 'Votre portefeuille de prospection, au même endroit.' },
  { id: 'calendrier', title: 'Calendrier', icon: CalendarDays, subtitle: 'Un espace pour organiser vos prochaines actions.' },
  { id: 'zones', title: 'Zones de prospection', icon: MapPin, subtitle: 'Votre territoire, organisé avec précision.' },
  { id: 'statistiques', title: 'Statistiques', icon: ChartNoAxesCombined, subtitle: 'Comprendre votre activité et ses résultats.' },
  { id: 'parametres', title: 'Paramètres', icon: Settings, subtitle: 'Un environnement personnel, entièrement local.' },
];
function App() {
  const [active, setActive] = useState(location.hash.slice(1) || pages[0].id);
  const [status, setStatus] = useState<'loading' | 'ok' | 'error'>('loading');
  useEffect(() => {
    const change = () => setActive(location.hash.slice(1) || pages[0].id);
    window.addEventListener('hashchange', change);
    return () => window.removeEventListener('hashchange', change);
  }, []);
  useEffect(() => {
    const controller = new AbortController();
    const timer = window.setTimeout(() => controller.abort(), 5000);
    fetch('/api/health', { signal: controller.signal }).then(r => { if (!r.ok) throw Error(); return r.json(); }).then(data => setStatus(data.status === 'ok' && data.database === 'ok' ? 'ok' : 'error')).catch(() => setStatus('error')).finally(() => clearTimeout(timer));
    return () => { clearTimeout(timer); controller.abort(); };
  }, []);
  const page = pages.find(p => p.id === active) || pages[0];
  const Icon = page.icon;
  return <div className="app">
    <a className="skip" href="#contenu">Aller au contenu</a>
    <aside>
      <div className="brand"><span className="brand-name">MORNY</span><span className="brand-sub">IMMOBILIER</span><span className="brand-line"/><small>ESPACE PROSPECTION</small></div>
      <nav aria-label="Navigation principale">{pages.map(p => <a key={p.id} href={'#' + p.id} aria-current={page.id === p.id ? 'page' : undefined}><p.icon size={19}/>{p.title}</a>)}</nav>
      <div className="sidebar-bottom"><ShieldCheck size={20}/><div>Données privées<small>Stockées sur cet ordinateur</small></div></div>
    </aside>
    <div className="workspace">
      <header><span>MORNY IMMOBILIER <span className="divider">/</span> <strong>Prospection</strong></span><span className="local"><Circle size={7} fill="currentColor"/> Usage local</span></header>
      <main id="contenu" tabIndex={-1}>
        <div className="heading"><div><p className="eyebrow">VOTRE ESPACE DE TRAVAIL</p><h1>{page.title}</h1><p className="subtitle">{page.subtitle}</p></div><span className="edition">Édition personnelle</span></div>
        {page.id === 'tableau-de-bord' ? <>
          <section className="welcome"><div><span className="eyebrow">MORNY IMMOBILIER · DEAUVILLE</span><h2>Chaque rencontre commence<br/>par une bonne organisation.</h2><p>Votre espace de prospection prend forme.<br/>Un cadre simple et confidentiel pour préparer la suite.</p><a className="button" href="#mes-biens">Découvrir mon espace <ArrowUpRight size={17}/></a></div><div className="architectural" aria-hidden="true"><Building2 size={140} strokeWidth={0.65}/><span>VOTRE TERRITOIRE, VOTRE EXPERTISE</span></div></section>
          <div className="section-title"><h2>Les essentiels</h2><span>Votre activité à venir</span></div>
          <section className="cards" aria-label="Modules à venir">{[{label:'Portefeuille', icon:House, text:'Vos biens à prospecter',target:'mes-biens'}, {label:'Organisation',icon:CalendarDays,text:'Vos actions et rendez-vous',target:'calendrier'}, {label:'Territoire',icon:MapPin,text:'Vos zones de prospection',target:'zones'}].map(c=><a className="card" key={c.target} href={'#'+c.target}><c.icon size={22}/><h3>{c.label}</h3><p>{c.text}</p><span>Module à venir <ArrowUpRight size={15}/></span></a>)}</section>
          <section className="notice"><ShieldCheck size={24}/><div><h3>Un espace qui vous appartient</h3><p>Aucune donnée transmise à un service externe. Après installation, l’application fonctionne sans connexion Internet.</p></div></section>
        </> : page.id === 'parametres' ? <section className="panel"><h2>Environnement local</h2><dl><div><dt>Serveur et base SQLite</dt><dd role="status">{status === 'ok' ? 'Opérationnels' : status === 'loading' ? 'Vérification en cours…' : 'Connexion indisponible — redémarrez l’application'}</dd></div><div><dt>Confidentialité</dt><dd>Données sur cet ordinateur uniquement</dd></div><div><dt>Identité visuelle</dt><dd>Emplacement réservé au logo officiel</dd></div></dl><p className="muted">Les options de sauvegarde et de personnalisation seront ajoutées dans une prochaine étape.</p></section> : <section className="empty"><span className="empty-icon"><Icon size={36} strokeWidth={1.3}/></span><p className="eyebrow">ESPACE PRÉPARÉ</p><h2>{page.title}</h2><p>{page.id === 'zones' ? 'Les neuf zones et leurs communes seront intégrées après réception de votre liste détaillée.' : 'Ce module sera développé lors d’une prochaine étape.'}<br/>Aucune donnée de démonstration n’a été ajoutée.</p><a href="#tableau-de-bord" className="button outline">Revenir au tableau de bord</a></section>}
        <footer><span>MORNY IMMOBILIER · Espace personnel</span><span role="status" className={'health ' + status}><Circle size={7} fill="currentColor"/>{status === 'ok' ? 'Environnement local opérationnel' : status === 'loading' ? 'Vérification du serveur…' : 'Serveur indisponible · vérifiez son démarrage'}</span></footer>
      </main>
    </div>
  </div>;
}
createRoot(document.getElementById('root')!).render(<App/>);
