import React, { useState } from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { 
  FileText, 
  Shield, 
  GitBranch, 
  BookOpen, 
  Scale, 
  History,
  Menu,
  X,
  Home,
  ArrowLeft,
  ExternalLink
} from 'lucide-react';

// Developer portal domain config
const PUBLIC_SITE = 'https://frekcore.com'; // Public site URL (placeholder until domain is configured)

const navItems = [
  { path: '/docs', label: 'Manifesto', icon: BookOpen, exact: true },
  { path: '/docs/architecture', label: 'Architecture', icon: GitBranch },
  { path: '/docs/spec', label: 'Specification', icon: FileText },
  { path: '/docs/governance', label: 'Governance', icon: Scale },
  { path: '/docs/changelog', label: 'Changelog', icon: History },
];

const DocsSidebar = ({ isOpen, onClose }) => {
  const location = useLocation();
  
  return (
    <>
      {isOpen && (
        <div 
          className="fixed inset-0 bg-black/80 z-40 md:hidden"
          onClick={onClose}
        />
      )}
      
      <aside className={`
        fixed inset-y-0 left-0 z-50 w-72 
        bg-[#0A0A0A] border-r border-zinc-800 
        flex flex-col
        transform transition-transform duration-200 ease-in-out
        ${isOpen ? 'translate-x-0' : '-translate-x-full'}
        md:translate-x-0
      `}>
        {/* Header */}
        <div className="h-16 flex items-center px-6 border-b border-zinc-800">
          <NavLink to="/" className="flex items-center gap-3">
            <div className="w-8 h-8 bg-[#00F0FF] flex items-center justify-center">
              <span className="font-mono font-bold text-black text-sm">F</span>
            </div>
            <span className="font-mono font-bold text-lg tracking-tight text-white">FREK</span>
          </NavLink>
          <button 
            className="ml-auto md:hidden p-2 text-zinc-500 hover:text-white"
            onClick={onClose}
          >
            <X className="w-5 h-5" />
          </button>
        </div>
        
        {/* Back to public site */}
        <div className="px-4 py-4 border-b border-zinc-800">
          <a 
            href="https://www.frekcore.com"
            className="flex items-center gap-2 text-zinc-500 hover:text-white font-mono text-xs uppercase tracking-wide transition-colors"
          >
            <ArrowLeft className="w-3 h-3" />
            Back to frekcore.com
          </a>
        </div>
        
        {/* Portal indicator */}
        <div className="px-4 py-3 bg-zinc-900/50 border-b border-zinc-800">
          <p className="font-mono text-[10px] uppercase tracking-widest text-[#00F0FF]">
            Developer Portal
          </p>
        </div>
        
        {/* Navigation */}
        <nav className="flex-1 py-6 overflow-y-auto">
          <div className="px-4">
            <p className="px-3 mb-3 text-[10px] font-mono uppercase tracking-widest text-zinc-600">
              Developer Documentation
            </p>
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = item.exact 
                ? location.pathname === item.path
                : location.pathname === item.path || location.pathname.startsWith(item.path + '/');
              
              return (
                <NavLink
                  key={item.path}
                  to={item.path}
                  onClick={onClose}
                  className={`
                    flex items-center gap-3 px-3 py-2.5 mb-1
                    font-mono text-sm transition-colors
                    ${isActive 
                      ? 'bg-zinc-900 text-white border-l-2 border-[#00F0FF] -ml-[2px] pl-[14px]' 
                      : 'text-zinc-500 hover:text-zinc-300 hover:bg-zinc-900/50'
                    }
                  `}
                >
                  <Icon className="w-4 h-4" strokeWidth={1.5} />
                  {item.label}
                </NavLink>
              );
            })}
          </div>
          
          <div className="px-4 mt-8">
            <p className="px-3 mb-3 text-[10px] font-mono uppercase tracking-widest text-zinc-600">
              Tools
            </p>
            <NavLink
              to="/verify"
              onClick={onClose}
              className="flex items-center gap-3 px-3 py-2.5 mb-1 font-mono text-sm text-[#00F0FF] hover:bg-zinc-900/50 transition-colors"
            >
              <Shield className="w-4 h-4" strokeWidth={1.5} />
              Verify Tool
            </NavLink>
          </div>
        </nav>
        
        {/* Footer */}
        <div className="p-4 border-t border-zinc-800">
          <p className="font-mono text-[10px] text-zinc-700 leading-relaxed mb-2">
            FREK v0.4 — Developer Portal
          </p>
          <p className="font-mono text-[10px] text-zinc-700">
            Infrastructure & Technical Documentation
          </p>
        </div>
      </aside>
    </>
  );
};

export function DocsLayout({ children }) {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  
  return (
    <div className="min-h-screen bg-[#050505]">
      <DocsSidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />
      
      {/* Mobile header */}
      <header className="fixed top-0 left-0 right-0 h-14 bg-[#0A0A0A] border-b border-zinc-800 flex items-center px-4 md:hidden z-30">
        <button 
          className="p-2 text-zinc-500 hover:text-white"
          onClick={() => setSidebarOpen(true)}
          data-testid="mobile-menu-btn"
        >
          <Menu className="w-5 h-5" />
        </button>
        <div className="flex items-center gap-2 ml-3">
          <div className="w-6 h-6 bg-[#00F0FF] flex items-center justify-center">
            <span className="font-mono font-bold text-black text-xs">F</span>
          </div>
          <span className="font-mono font-bold text-white">FREK</span>
          <span className="font-mono text-xs text-zinc-600">Docs</span>
        </div>
      </header>
      
      {/* Main content */}
      <main className="md:ml-72 min-h-screen pt-14 md:pt-0">
        {children}
      </main>
    </div>
  );
}

export default DocsLayout;
