import { motion } from 'framer-motion';

const steps = [
  { num: 1, label: 'Identité' },
  { num: 2, label: 'Tracklist' },
  { num: 3, label: 'Empreinte' },
  { num: 4, label: 'Génération' },
];

export function WizardStepper({ currentStep, onStepClick }) {
  return (
    <div className="w-full py-8">
      <div className="flex items-center justify-between max-w-2xl mx-auto px-4">
        {steps.map((step, index) => (
          <div key={step.num} className="flex items-center">
            {/* Step Circle */}
            <button
              onClick={() => onStepClick?.(step.num)}
              disabled={step.num > currentStep}
              className={`
                relative flex items-center justify-center w-10 h-10 rounded-full 
                font-display text-lg transition-all duration-300
                ${step.num === currentStep
                  ? 'bg-terra text-fwhite'
                  : step.num < currentStep
                  ? 'bg-terra/30 text-terra cursor-pointer hover:bg-terra/50'
                  : 'bg-dark border border-dim/30 text-dim cursor-not-allowed'
                }
              `}
            >
              {step.num < currentStep ? (
                <span className="text-sm">✓</span>
              ) : (
                step.num
              )}
            </button>
            
            {/* Step Label (hidden on mobile) */}
            <span
              className={`
                hidden sm:block ml-3 font-mono text-xs uppercase tracking-wider
                ${step.num === currentStep ? 'text-terra' : 'text-dim'}
              `}
            >
              {step.label}
            </span>
            
            {/* Connector Line */}
            {index < steps.length - 1 && (
              <div className="flex-1 mx-4 h-px bg-dim/20 min-w-[2rem] sm:min-w-[4rem]">
                <motion.div
                  className="h-full bg-terra"
                  initial={{ width: 0 }}
                  animate={{ width: step.num < currentStep ? '100%' : 0 }}
                  transition={{ duration: 0.3 }}
                />
              </div>
            )}
          </div>
        ))}
      </div>
      
      {/* Mobile Step Label */}
      <div className="sm:hidden text-center mt-4">
        <span className="font-mono text-sm text-terra">
          Étape {currentStep} — {steps[currentStep - 1]?.label}
        </span>
      </div>
    </div>
  );
}

export default WizardStepper;
