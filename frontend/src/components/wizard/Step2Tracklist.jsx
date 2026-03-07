import { motion, AnimatePresence } from 'framer-motion';

export function Step2Tracklist({
  tracklist,
  addTrack,
  updateTrack,
  removeTrack,
  moveTrackUp,
  moveTrackDown,
}) {
  return (
    <div className="space-y-6">
      <div>
        <h3 className="font-display text-2xl text-fwhite mb-2">Tracklist</h3>
        <p className="font-body text-mid text-sm mb-6">
          La tracklist renforce la valeur probatoire de l&apos;attestation. Elle n&apos;est pas obligatoire mais fortement recommandée.
        </p>
      </div>

      {/* Tracks List */}
      <AnimatePresence mode="popLayout">
        {tracklist.map((track, index) => (
          <motion.div
            key={index}
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, x: -20 }}
            className="p-4 bg-[#0a0a0a] border border-[#222] space-y-4"
          >
            {/* Track Header */}
            <div className="flex items-center justify-between">
              <span className="font-display text-xl text-terra">
                #{track.position}
              </span>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => moveTrackUp(index)}
                  disabled={index === 0}
                  className="w-8 h-8 flex items-center justify-center border border-[#333] text-mid hover:text-terra hover:border-terra disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
                >
                  ↑
                </button>
                <button
                  onClick={() => moveTrackDown(index)}
                  disabled={index === tracklist.length - 1}
                  className="w-8 h-8 flex items-center justify-center border border-[#333] text-mid hover:text-terra hover:border-terra disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
                >
                  ↓
                </button>
                <button
                  onClick={() => removeTrack(index)}
                  className="w-8 h-8 flex items-center justify-center border border-[#333] text-mid hover:text-red-400 hover:border-red-400 transition-colors"
                >
                  ×
                </button>
              </div>
            </div>

            {/* Track Fields */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block font-mono text-xs text-dim mb-1">
                  Titre
                </label>
                <input
                  type="text"
                  value={track.title}
                  onChange={(e) => updateTrack(index, { title: e.target.value })}
                  placeholder="Titre du morceau"
                  className="w-full px-3 py-2 bg-[#111] border border-[#333] font-body text-light text-sm focus:outline-none focus:border-terra transition-colors"
                />
              </div>
              <div>
                <label className="block font-mono text-xs text-dim mb-1">
                  Artiste
                </label>
                <input
                  type="text"
                  value={track.artist}
                  onChange={(e) => updateTrack(index, { artist: e.target.value })}
                  placeholder="Nom de l'artiste"
                  className="w-full px-3 py-2 bg-[#111] border border-[#333] font-body text-light text-sm focus:outline-none focus:border-terra transition-colors"
                />
              </div>
              <div>
                <label className="block font-mono text-xs text-dim mb-1">
                  ISRC <span className="text-dim">(optionnel)</span>
                </label>
                <input
                  type="text"
                  value={track.isrc}
                  onChange={(e) => updateTrack(index, { isrc: e.target.value })}
                  placeholder="FR-ABC-26-00001"
                  className="w-full px-3 py-2 bg-[#111] border border-[#333] font-mono text-light text-sm focus:outline-none focus:border-terra transition-colors"
                />
              </div>
              <div>
                <label className="block font-mono text-xs text-dim mb-1">
                  Temps de début <span className="text-dim">(MM:SS)</span>
                </label>
                <input
                  type="text"
                  value={track.start_time}
                  onChange={(e) => updateTrack(index, { start_time: e.target.value })}
                  placeholder="00:00"
                  className="w-full px-3 py-2 bg-[#111] border border-[#333] font-mono text-light text-sm focus:outline-none focus:border-terra transition-colors"
                />
              </div>
            </div>
          </motion.div>
        ))}
      </AnimatePresence>

      {/* Empty State */}
      {tracklist.length === 0 && (
        <div className="p-12 border-2 border-dashed border-[#333] text-center">
          <p className="font-body text-dim mb-4">Aucun titre ajouté</p>
          <p className="font-mono text-xs text-dim/60">
            Cliquez sur "Ajouter un titre" pour commencer
          </p>
        </div>
      )}

      {/* Add Track Button */}
      <button
        onClick={addTrack}
        className="w-full py-4 border-2 border-dashed border-terra/30 text-terra hover:bg-terra/5 hover:border-terra/50 transition-colors font-mono text-sm"
      >
        + Ajouter un titre
      </button>

      {/* Skip Notice */}
      <div className="p-4 bg-navy/30 border-l-2 border-gold/50">
        <p className="font-mono text-xs text-gold">
          💡 Cette étape est optionnelle. Vous pouvez passer à l&apos;étape suivante même sans tracklist.
        </p>
      </div>
    </div>
  );
}

export default Step2Tracklist;
