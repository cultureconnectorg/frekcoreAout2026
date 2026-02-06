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
  ExternalLink
} from 'lucide-react';

const navItems = [
  { path: '/', label: 'Accueil', icon: Shield, exact: true },
  { path: '/docs', label: 'Manifeste', icon: BookOpen },
  { path: '/architecture', label: 'Architecture', icon: GitBranch },
  { path: '/spec', label: 'Spécification', icon: FileText },
  { path: '/governance', label: 'Gouvernance', icon: Scale },
  { path: '/changelog', label: 'Changelog', icon: History },
];

const Sidebar = ({ isOpen, onClose }) => {
  const location = useLocation();
  
  return (
    <>
      {/* Mobile overlay */}
      {isOpen && (
        <div 
          className="fixed inset-0 bg-black/80 z-40 md:hidden"
          onClick={onClose}
        />
      )}
      
      {/* Sidebar */}
      <aside className={`
        fixed inset-y-0 left-0 z-50 w-64 
        bg-[#0A0A0A] border-r border-zinc-800 
        flex flex-col
        transform transition-transform duration-200 ease-in-out
        ${isOpen ? 'translate-x-0' : '-translate-x-full'}
        md:translate-x-0
      `}>
        {/* Logo */}
        <div className="h-16 flex items-center px-6 border-b border-zinc-800">
          <NavLink to="/" className="flex items-center gap-3" onClick={onClose}>
            <div className="w-8 h-8 bg-[#00F0FF] flex items-center justify-center">
              <span className="font-mono font-bold text-black text-sm">F</span>
            </div>
            <span className="font-mono font-bold text-lg tracking-tight">FREK</span>
            <span className="font-mono text-xs text-zinc-500 ml-1">v0.4</span>
          </NavLink>
          <button 
            className="ml-auto md:hidden p-2 text-zinc-500 hover:text-white"
            onClick={onClose}
          >
            <X className="w-5 h-5" />
          </button>
        </div>
        
        {/* Navigation */}
        <nav className="flex-1 py-4 overflow-y-auto">
          <div className="px-3">
            <p className="px-3 mb-2 text-[10px] font-mono uppercase tracking-widest text-zinc-600">
              Documentation
            </p>
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = item.exact 
                ? location.pathname === item.path
                : location.pathname.startsWith(item.path);
              
              return (
                <NavLink
                  key={item.path}
                  to={item.path}
                  onClick={onClose}
                  className={`
                    flex items-center gap-3 px-3 py-2 mb-1
                    font-mono text-sm transition-colors
                    ${isActive 
                      ? 'bg-zinc-900 text-white border-r-2 border-[#00F0FF]' 
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
          
          <div className="px-3 mt-6">
            <p className="px-3 mb-2 text-[10px] font-mono uppercase tracking-widest text-zinc-600">
              Outils
            </p>
            <NavLink
              to="/verify"
              onClick={onClose}
              className={`
                flex items-center gap-3 px-3 py-2 mb-1
                font-mono text-sm transition-colors
                ${location.pathname === '/verify'
                  ? 'bg-zinc-900 text-[#00F0FF] border-r-2 border-[#00F0FF]' 
                  : 'text-zinc-500 hover:text-[#00F0FF] hover:bg-zinc-900/50'
                }
              `}
            >
              <Shield className="w-4 h-4" strokeWidth={1.5} />
              Vérifier
            </NavLink>
          </div>
        </nav>
        
        {/* Footer */}
        <div className="p-4 border-t border-zinc-800">
          <p className="font-mono text-[10px] text-zinc-600 leading-relaxed">
            FREK est un standard ouvert.<br/>
            Pas de tracking. Pas de cloud.
          </p>
        </div>
      </aside>
    </>
  );
};

export function Layout({ children }) {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  
  return (
    <div className="min-h-screen bg-[#050505]">
      <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />
      
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
          <span className="font-mono font-bold">FREK</span>
        </div>
      </header>
      
      {/* Main content */}
      <main className="md:ml-64 min-h-screen pt-14 md:pt-0">
        {children}
      </main>
    </div>
  );
}

export default Layout;
