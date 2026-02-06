import React, { createContext, useContext, useState, useEffect } from 'react';
import { LANGUAGES, getTranslation, getLanguageInfo } from './i18n';

const LanguageContext = createContext();

export function LanguageProvider({ children }) {
  const [lang, setLang] = useState(() => {
    // Get from localStorage or default to 'en'
    if (typeof window !== 'undefined') {
      return localStorage.getItem('frek-lang') || 'en';
    }
    return 'en';
  });

  const t = getTranslation(lang);
  const langInfo = getLanguageInfo(lang);

  useEffect(() => {
    // Save to localStorage
    localStorage.setItem('frek-lang', lang);
    
    // Set document direction for RTL support
    document.documentElement.dir = langInfo.dir;
    document.documentElement.lang = lang;
  }, [lang, langInfo.dir]);

  const switchLanguage = (newLang) => {
    if (LANGUAGES[newLang]) {
      setLang(newLang);
    }
  };

  return (
    <LanguageContext.Provider value={{ lang, t, langInfo, switchLanguage, LANGUAGES }}>
      {children}
    </LanguageContext.Provider>
  );
}

export function useLanguage() {
  const context = useContext(LanguageContext);
  if (!context) {
    throw new Error('useLanguage must be used within a LanguageProvider');
  }
  return context;
}

export default LanguageContext;
