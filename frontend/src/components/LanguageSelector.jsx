import React, { useState, useRef, useEffect } from 'react';
import { ChevronDown, Globe } from 'lucide-react';
import { useLanguage } from '../lib/LanguageContext';

export function LanguageSelector() {
  const { lang, switchLanguage, LANGUAGES, langInfo } = useLanguage();
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef(null);

  useEffect(() => {
    function handleClickOutside(event) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 px-3 py-2 text-zinc-400 hover:text-white transition-colors font-mono text-sm"
        data-testid="language-selector"
      >
        <Globe className="w-4 h-4" />
        <span className="hidden sm:inline">{langInfo.name}</span>
        <ChevronDown className={`w-3 h-3 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </button>

      {isOpen && (
        <div className="absolute top-full right-0 mt-2 bg-[#0A0A0A] border border-zinc-800 shadow-xl z-50 min-w-[140px]">
          {Object.values(LANGUAGES).map((language) => (
            <button
              key={language.code}
              onClick={() => {
                switchLanguage(language.code);
                setIsOpen(false);
              }}
              className={`
                w-full flex items-center gap-3 px-4 py-3 text-left font-mono text-sm transition-colors
                ${lang === language.code 
                  ? 'bg-zinc-900 text-[#00F0FF]' 
                  : 'text-zinc-400 hover:text-white hover:bg-zinc-900/50'
                }
              `}
              dir={language.dir}
            >
              <span>{language.flag}</span>
              <span>{language.name}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

export default LanguageSelector;
