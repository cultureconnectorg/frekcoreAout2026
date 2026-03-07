import { Link } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { useWizardState } from '../hooks/useWizardState';
import { WizardStepper } from '../components/wizard/WizardStepper';
import { Step1Identity } from '../components/wizard/Step1Identity';
import { Step2Tracklist } from '../components/wizard/Step2Tracklist';
import { Step3Fingerprint } from '../components/wizard/Step3Fingerprint';
import { Step4Review } from '../components/wizard/Step4Review';
import { validateWizardState } from '../utils/frek-generator';

const stepVariants = {
  enter: { opacity: 0, x: 20 },
  center: { opacity: 1, x: 0 },
  exit: { opacity: 0, x: -20 },
};

export function Generate() {
  const {
    state,
    setStep,
    nextStep,
    prevStep,
    updateArtist,
    updateEvent,
    addTrack,
    updateTrack,
    removeTrack,
    moveTrackUp,
    moveTrackDown,
    setAudioFile,
    setFingerprint,
    setMixId,
    setCreatedAt,
    setSignature,
    setGenerating,
    setComplete,
    setErrors,
    reset,
  } = useWizardState();

  const canProceed = () => {
    if (state.currentStep === 1) {
      return state.artist.name?.trim() && state.event.name?.trim() && state.event.date;
    }
    return true;
  };

  const handleNext = () => {
    if (canProceed()) {
      nextStep();
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  };

  const handlePrev = () => {
    prevStep();
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleStepClick = (step) => {
    if (step <= state.currentStep) {
      setStep(step);
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-white via-slate-50 to-gray-100">
      {/* Header */}
      <header className="fixed top-0 left-0 right-0 z-50 bg-white/80 backdrop-blur-xl border-b border-slate-200/50 shadow-sm">
        <div className="max-w-5xl mx-auto px-6 h-16 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2">
            <img 
              src="/frek-logo.png" 
              alt="FREK" 
              className="h-8 w-auto"
            />
            <span className="font-display text-xl tracking-wider text-[#2cc4f5]">FREK</span>
          </Link>
          <span className="font-mono text-xs text-slate-500 hidden sm:block">
            Générateur d&apos;attestation
          </span>
          <Link to="/" className="font-mono text-xs text-slate-400 hover:text-[#2cc4f5] transition-colors">
            Retour
          </Link>
        </div>
      </header>

      {/* Main Content */}
      <main className="pt-16">
        {/* Stepper */}
        <WizardStepper currentStep={state.currentStep} onStepClick={handleStepClick} />

        {/* Step Content */}
        <div className="max-w-3xl mx-auto px-6 pb-32">
          <AnimatePresence mode="wait">
            {state.currentStep === 1 && (
              <motion.div
                key="step1"
                variants={stepVariants}
                initial="enter"
                animate="center"
                exit="exit"
                transition={{ duration: 0.3 }}
              >
                <Step1Identity
                  state={state}
                  updateArtist={updateArtist}
                  updateEvent={updateEvent}
                  errors={state.errors}
                />
              </motion.div>
            )}

            {state.currentStep === 2 && (
              <motion.div
                key="step2"
                variants={stepVariants}
                initial="enter"
                animate="center"
                exit="exit"
                transition={{ duration: 0.3 }}
              >
                <Step2Tracklist
                  tracklist={state.tracklist}
                  addTrack={addTrack}
                  updateTrack={updateTrack}
                  removeTrack={removeTrack}
                  moveTrackUp={moveTrackUp}
                  moveTrackDown={moveTrackDown}
                />
              </motion.div>
            )}

            {state.currentStep === 3 && (
              <motion.div
                key="step3"
                variants={stepVariants}
                initial="enter"
                animate="center"
                exit="exit"
                transition={{ duration: 0.3 }}
              >
                <Step3Fingerprint
                  state={state}
                  setFingerprint={setFingerprint}
                  setAudioFile={setAudioFile}
                />
              </motion.div>
            )}

            {state.currentStep === 4 && (
              <motion.div
                key="step4"
                variants={stepVariants}
                initial="enter"
                animate="center"
                exit="exit"
                transition={{ duration: 0.3 }}
              >
                <Step4Review
                  state={state}
                  setMixId={setMixId}
                  setCreatedAt={setCreatedAt}
                  setSignature={setSignature}
                  setGenerating={setGenerating}
                  setComplete={setComplete}
                />
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </main>

      {/* Fixed Bottom Navigation */}
      {!state.isComplete && (
        <div className="fixed bottom-0 left-0 right-0 bg-white/80 backdrop-blur-xl border-t border-slate-200/50 shadow-lg">
          <div className="max-w-3xl mx-auto px-6 py-4 flex items-center justify-between">
            <button
              onClick={handlePrev}
              disabled={state.currentStep === 1}
              className="px-6 py-3 border border-slate-300 text-slate-600 font-mono text-sm uppercase tracking-wider hover:border-[#2cc4f5] hover:text-[#2cc4f5] disabled:opacity-30 disabled:cursor-not-allowed transition-colors rounded-lg"
            >
              ← Précédent
            </button>

            <span className="font-mono text-xs text-slate-400">
              {state.currentStep} / 4
            </span>

            {state.currentStep < 4 ? (
              <button
                onClick={handleNext}
                disabled={!canProceed()}
                className="px-6 py-3 bg-[#2cc4f5] text-white font-mono text-sm uppercase tracking-wider hover:bg-[#1a9fd4] disabled:opacity-50 disabled:cursor-not-allowed transition-colors rounded-lg shadow-lg shadow-[#2cc4f5]/20"
              >
                Suivant →
              </button>
            ) : (
              <div className="w-32" /> // Placeholder for alignment
            )}
          </div>
        </div>
      )}

      {/* Success State - New Attestation Button */}
      {state.isComplete && (
        <div className="fixed bottom-0 left-0 right-0 bg-white/80 backdrop-blur-xl border-t border-green-200/50 shadow-lg">
          <div className="max-w-3xl mx-auto px-6 py-4 flex items-center justify-center gap-4">
            <button
              onClick={reset}
              className="px-6 py-3 border border-[#2cc4f5] text-[#2cc4f5] font-mono text-sm uppercase tracking-wider hover:bg-[#2cc4f5]/10 transition-colors rounded-lg"
            >
              Nouvelle attestation
            </button>
            <Link
              to="/"
              className="px-6 py-3 border border-slate-300 text-slate-500 font-mono text-sm uppercase tracking-wider hover:text-slate-700 hover:border-slate-400 transition-colors rounded-lg"
            >
              Accueil
            </Link>
          </div>
        </div>
      )}
    </div>
  );
}

export default Generate;
