import { useTranslation } from 'react-i18next';
import { languages } from '../../i18n';

export function LanguageSwitcher() {
  const { i18n } = useTranslation();
  const currentLang = languages.find(l => l.code === i18n.language) || languages[0];

  const handleChange = (e) => {
    const lang = e.target.value;
    i18n.changeLanguage(lang);
    // Update document direction for RTL languages
    const isRtl = languages.find(l => l.code === lang)?.rtl;
    document.documentElement.dir = isRtl ? 'rtl' : 'ltr';
  };

  return (
    <select
      value={i18n.language}
      onChange={handleChange}
      className="bg-transparent border border-terra/30 text-mid font-mono text-xs px-2 py-1 focus:outline-none focus:border-terra cursor-pointer hover:text-terra transition-colors"
      aria-label="Select language"
    >
      {languages.map((lang) => (
        <option key={lang.code} value={lang.code} className="bg-dark text-light">
          {lang.flag} {lang.name}
        </option>
      ))}
    </select>
  );
}

export default LanguageSwitcher;
