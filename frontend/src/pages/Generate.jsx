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
    <div className="min-h-screen bg-dark">
      {/* Header */}
      <header className="fixed top-0 left-0 right-0 z-50 bg-dark/95 backdrop-blur-md border-b border-terra/20">
        <div className="max-w-5xl mx-auto px-6 h-16 flex items-center justify-between">
          <Link to="/" className="flex items-baseline gap-0.5">
            <span className="font-display text-2xl text-terra">FREK</span>
            <span className="font-display text-sm text-gold">®</span>
          </Link>
          <span className="font-mono text-xs text-mid hidden sm:block">
            Générateur d&apos;attestation
          </span>
          <Link to="/" className="font-mono text-xs text-dim hover:text-terra transition-colors">
            Retour au site
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
        <div className="fixed bottom-0 left-0 right-0 bg-dark/95 backdrop-blur-md border-t border-terra/20">
          <div className="max-w-3xl mx-auto px-6 py-4 flex items-center justify-between">
            <button
              onClick={handlePrev}
              disabled={state.currentStep === 1}
              className="px-6 py-3 border border-terra/30 text-terra font-mono text-sm uppercase tracking-wider hover:bg-terra/10 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
            >
              ← Précédent
            </button>

            <span className="font-mono text-xs text-dim">
              {state.currentStep} / 4
            </span>

            {state.currentStep < 4 ? (
              <button
                onClick={handleNext}
                disabled={!canProceed()}
                className="px-6 py-3 bg-terra text-fwhite font-mono text-sm uppercase tracking-wider hover:bg-terra/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
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
        <div className="fixed bottom-0 left-0 right-0 bg-dark/95 backdrop-blur-md border-t border-fgreen/30">
          <div className="max-w-3xl mx-auto px-6 py-4 flex items-center justify-center gap-4">
            <button
              onClick={reset}
              className="px-6 py-3 border border-terra text-terra font-mono text-sm uppercase tracking-wider hover:bg-terra/10 transition-colors"
            >
              Nouvelle attestation
            </button>
            <Link
              to="/#verifier"
              className="px-6 py-3 border border-dim/30 text-dim font-mono text-sm uppercase tracking-wider hover:text-mid hover:border-dim/50 transition-colors"
            >
              Vérifier
            </Link>
          </div>
        </div>
      )}
    </div>
  );
}

export default Generate;
