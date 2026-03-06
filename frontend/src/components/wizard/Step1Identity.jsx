// Territory list with Caribbean/France first
export const territories = [
  { code: 'MQ', name: 'Martinique' },
  { code: 'GP', name: 'Guadeloupe' },
  { code: 'GF', name: 'Guyane française' },
  { code: 'RE', name: 'La Réunion' },
  { code: 'FR', name: 'France' },
  { code: 'BE', name: 'Belgique' },
  { code: 'CH', name: 'Suisse' },
  { code: 'CA', name: 'Canada' },
  { code: 'HT', name: 'Haïti' },
  { code: 'DO', name: 'République dominicaine' },
  { code: 'CU', name: 'Cuba' },
  { code: 'JM', name: 'Jamaïque' },
  { code: 'TT', name: 'Trinité-et-Tobago' },
  { code: 'BB', name: 'Barbade' },
  { code: 'LC', name: 'Sainte-Lucie' },
  { code: 'DM', name: 'Dominique' },
  { code: 'VC', name: 'Saint-Vincent' },
  { code: 'GD', name: 'Grenade' },
  { code: 'AG', name: 'Antigua-et-Barbuda' },
  { code: 'KN', name: 'Saint-Kitts-et-Nevis' },
  { code: 'PR', name: 'Porto Rico' },
  { code: 'VI', name: 'Îles Vierges' },
  { code: 'US', name: 'États-Unis' },
  { code: 'GB', name: 'Royaume-Uni' },
  { code: 'DE', name: 'Allemagne' },
  { code: 'ES', name: 'Espagne' },
  { code: 'IT', name: 'Italie' },
  { code: 'NL', name: 'Pays-Bas' },
  { code: 'PT', name: 'Portugal' },
  { code: 'BR', name: 'Brésil' },
  { code: 'CO', name: 'Colombie' },
  { code: 'MX', name: 'Mexique' },
  { code: 'AR', name: 'Argentine' },
  { code: 'CL', name: 'Chili' },
  { code: 'JP', name: 'Japon' },
  { code: 'AU', name: 'Australie' },
  { code: 'XX', name: 'Autre / International' },
];

export const contexts = [
  { value: 'live', label: 'Live (festival, club, événement)' },
  { value: 'studio', label: 'Studio (enregistrement)' },
  { value: 'radio', label: 'Radio (émission)' },
  { value: 'stream', label: 'Stream (Twitch, YouTube, etc.)' },
  { value: 'podcast', label: 'Podcast' },
  { value: 'compilation', label: 'Compilation' },
];

export function Step1Identity({ state, updateArtist, updateEvent, errors }) {
  return (
    <div className="space-y-8">
      {/* Artist Section */}
      <div>
        <h3 className="font-display text-2xl text-fwhite mb-6">Artiste / DJ</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block font-mono text-xs text-mid mb-2">
              Nom de scène <span className="text-terra">*</span>
            </label>
            <input
              type="text"
              value={state.artist.name}
              onChange={(e) => updateArtist({ name: e.target.value })}
              placeholder="DJ Kathy"
              className={`
                w-full px-4 py-3 bg-[#111] border font-body text-light
                focus:outline-none focus:border-terra transition-colors
                ${errors?.artistName ? 'border-red-500' : 'border-[#333]'}
              `}
            />
            {errors?.artistName && (
              <p className="mt-1 font-mono text-xs text-red-400">{errors.artistName}</p>
            )}
          </div>
          
          <div>
            <label className="block font-mono text-xs text-mid mb-2">
              Nom légal <span className="text-dim">(optionnel)</span>
            </label>
            <input
              type="text"
              value={state.artist.legal_name}
              onChange={(e) => updateArtist({ legal_name: e.target.value })}
              placeholder="Kathy-Liana Bravo"
              className="w-full px-4 py-3 bg-[#111] border border-[#333] font-body text-light focus:outline-none focus:border-terra transition-colors"
            />
          </div>
          
          <div className="md:col-span-2">
            <label className="block font-mono text-xs text-mid mb-2">
              Territoire <span className="text-terra">*</span>
            </label>
            <select
              value={state.artist.territory}
              onChange={(e) => updateArtist({ territory: e.target.value })}
              className="w-full px-4 py-3 bg-[#111] border border-[#333] font-body text-light focus:outline-none focus:border-terra transition-colors"
            >
              {territories.map((t) => (
                <option key={t.code} value={t.code}>
                  {t.code} — {t.name}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Event Section */}
      <div>
        <h3 className="font-display text-2xl text-fwhite mb-6">Événement / Performance</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="md:col-span-2">
            <label className="block font-mono text-xs text-mid mb-2">
              Nom de l&apos;événement <span className="text-terra">*</span>
            </label>
            <input
              type="text"
              value={state.event.name}
              onChange={(e) => updateEvent({ name: e.target.value })}
              placeholder="Culture Connect 2026 — Scène Chimin"
              className={`
                w-full px-4 py-3 bg-[#111] border font-body text-light
                focus:outline-none focus:border-terra transition-colors
                ${errors?.eventName ? 'border-red-500' : 'border-[#333]'}
              `}
            />
            {errors?.eventName && (
              <p className="mt-1 font-mono text-xs text-red-400">{errors.eventName}</p>
            )}
          </div>
          
          <div>
            <label className="block font-mono text-xs text-mid mb-2">
              Date <span className="text-terra">*</span>
            </label>
            <input
              type="date"
              value={state.event.date}
              onChange={(e) => updateEvent({ date: e.target.value })}
              className="w-full px-4 py-3 bg-[#111] border border-[#333] font-body text-light focus:outline-none focus:border-terra transition-colors"
            />
          </div>
          
          <div>
            <label className="block font-mono text-xs text-mid mb-2">
              Heure de début <span className="text-dim">(optionnel)</span>
            </label>
            <input
              type="time"
              value={state.event.start_time}
              onChange={(e) => updateEvent({ start_time: e.target.value })}
              className="w-full px-4 py-3 bg-[#111] border border-[#333] font-body text-light focus:outline-none focus:border-terra transition-colors"
            />
          </div>
          
          <div>
            <label className="block font-mono text-xs text-mid mb-2">
              Lieu / Venue <span className="text-dim">(optionnel)</span>
            </label>
            <input
              type="text"
              value={state.event.venue}
              onChange={(e) => updateEvent({ venue: e.target.value })}
              placeholder="La Savane"
              className="w-full px-4 py-3 bg-[#111] border border-[#333] font-body text-light focus:outline-none focus:border-terra transition-colors"
            />
          </div>
          
          <div>
            <label className="block font-mono text-xs text-mid mb-2">
              Ville <span className="text-dim">(optionnel)</span>
            </label>
            <input
              type="text"
              value={state.event.city}
              onChange={(e) => updateEvent({ city: e.target.value })}
              placeholder="Fort-de-France"
              className="w-full px-4 py-3 bg-[#111] border border-[#333] font-body text-light focus:outline-none focus:border-terra transition-colors"
            />
          </div>
          
          <div className="md:col-span-2">
            <label className="block font-mono text-xs text-mid mb-2">
              Contexte <span className="text-terra">*</span>
            </label>
            <select
              value={state.event.context}
              onChange={(e) => updateEvent({ context: e.target.value })}
              className="w-full px-4 py-3 bg-[#111] border border-[#333] font-body text-light focus:outline-none focus:border-terra transition-colors"
            >
              {contexts.map((c) => (
                <option key={c.value} value={c.value}>
                  {c.label}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Step1Identity;
