import { motion } from 'framer-motion';
import { useTranslation } from 'react-i18next';

export function WizardStepper({ currentStep, onStepClick }) {
  const { t } = useTranslation();
  
  const steps = [
    { num: 1, label: t('wizard.steps.identity') },
    { num: 2, label: t('wizard.steps.tracklist') },
    { num: 3, label: t('wizard.steps.fingerprint') },
    { num: 4, label: t('wizard.steps.generation') },
  ];

  return (
    <nav 
      className="w-full py-8"
      role="navigation"
      aria-label={t('wizard.generator')}
    >
      <ol 
        className="flex items-center justify-between max-w-2xl mx-auto px-4"
        role="list"
      >
        {steps.map((step, index) => (
          <li key={step.num} className="flex items-center" role="listitem">
            {/* Step Circle */}
            <button
              onClick={() => onStepClick?.(step.num)}
              disabled={step.num > currentStep}
              aria-current={step.num === currentStep ? 'step' : undefined}
              aria-label={`${step.label} - ${t('wizard.steps.identity').includes('Étape') ? 'Étape' : 'Step'} ${step.num}${step.num < currentStep ? ` (${t('common.success').toLowerCase()})` : ''}`}
              className={`
                relative flex items-center justify-center w-10 h-10 rounded-full 
                font-display text-lg transition-all duration-300
                focus:outline-none focus:ring-2 focus:ring-terra focus:ring-offset-2 focus:ring-offset-dark
                ${step.num === currentStep
                  ? 'bg-terra text-fwhite'
                  : step.num < currentStep
                  ? 'bg-terra/30 text-terra cursor-pointer hover:bg-terra/50'
                  : 'bg-dark border border-dim/30 text-dim cursor-not-allowed'
                }
              `}
            >
              {step.num < currentStep ? (
                <span className="text-sm" aria-hidden="true">✓</span>
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
              aria-hidden="true"
            >
              {step.label}
            </span>
            
            {/* Connector Line */}
            {index < steps.length - 1 && (
              <div 
                className="flex-1 mx-4 h-px bg-dim/20 min-w-[2rem] sm:min-w-[4rem]"
                aria-hidden="true"
              >
                <motion.div
                  className="h-full bg-terra"
                  initial={{ width: 0 }}
                  animate={{ width: step.num < currentStep ? '100%' : 0 }}
                  transition={{ duration: 0.3 }}
                />
              </div>
            )}
          </li>
        ))}
      </ol>
      
      {/* Mobile Step Label - Screen reader accessible */}
      <div className="sm:hidden text-center mt-4">
        <span className="font-mono text-sm text-terra">
          {t('wizard.steps.identity').includes('Étape') ? 'Étape' : 'Step'} {currentStep} — {steps[currentStep - 1]?.label}
        </span>
      </div>
    </nav>
  );
}

export default WizardStepper;
