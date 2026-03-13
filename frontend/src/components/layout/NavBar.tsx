import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { FilterIcon, BookOpen, Settings, Edit3, Heart } from 'lucide-react';

const NavBar: React.FC = () => {
  const location = useLocation();
  
  const isActive = (path: string) => {
    return location.pathname === path;
  };
  
  return (
    <nav className="fixed top-0 left-0 right-0 bg-[#1C1C1E] text-white z-10 shadow-md backdrop-blur-lg bg-opacity-90">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          <Link to="/" className="flex items-center space-x-2">
            <BookOpen className="w-6 h-6 text-[#0A84FF]" />
            <span className="font-semibold text-lg">每日精读</span>
          </Link>
          
          <div className="hidden md:flex space-x-4">
            <NavLink to="/" active={isActive('/')}>
              <FilterIcon className="w-5 h-5 mr-1" />
              <span>精选内容</span>
            </NavLink>
            
            <NavLink to="/favorites" active={isActive('/favorites')}>
              <Heart className="w-5 h-5 mr-1" />
              <span>收藏夹</span>
            </NavLink>
            
            <NavLink to="/sources" active={isActive('/sources')}>
              <Edit3 className="w-5 h-5 mr-1" />
              <span>信息源</span>
            </NavLink>
            
            <NavLink to="/settings" active={isActive('/settings')}>
              <Settings className="w-5 h-5 mr-1" />
              <span>提示词预设</span>
            </NavLink>
          </div>
          
          <div className="md:hidden flex items-center">
            <MobileMenu />
          </div>
        </div>
      </div>
    </nav>
  );
};

const NavLink: React.FC<{
  to: string;
  active: boolean;
  children: React.ReactNode;
}> = ({ to, active, children }) => {
  return (
    <Link
      to={to}
      className={`flex items-center px-3 py-2 rounded-md transition duration-150 ${
        active
          ? 'bg-[#2C2C2E] text-[#0A84FF]'
          : 'text-gray-300 hover:bg-[#2C2C2E] hover:text-[#0A84FF]'
      }`}
    >
      {children}
    </Link>
  );
};

const MobileMenu: React.FC = () => {
  const [isOpen, setIsOpen] = React.useState(false);
  
  return (
    <div>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="text-gray-300 hover:text-[#0A84FF] focus:outline-none"
      >
        <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          {isOpen ? (
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          ) : (
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
          )}
        </svg>
      </button>
      
      {isOpen && (
        <div className="absolute top-16 right-0 left-0 bg-[#1C1C1E] bg-opacity-90 backdrop-blur-lg shadow-md">
          <div className="px-2 pt-2 pb-3 space-y-1">
            <MobileNavLink to="/" label="精选内容" icon={<FilterIcon className="w-5 h-5 mr-2" />} />
            <MobileNavLink to="/favorites" label="收藏夹" icon={<Heart className="w-5 h-5 mr-2" />} />
            <MobileNavLink to="/sources" label="信息源" icon={<Edit3 className="w-5 h-5 mr-2" />} />
            <MobileNavLink to="/settings" label="提示词预设" icon={<Settings className="w-5 h-5 mr-2" />} />
          </div>
        </div>
      )}
    </div>
  );
};

const MobileNavLink: React.FC<{
  to: string;
  label: string;
  icon: React.ReactNode;
}> = ({ to, label, icon }) => {
  const location = useLocation();
  const active = location.pathname === to;
  
  return (
    <Link
      to={to}
      className={`flex items-center px-3 py-2 rounded-md transition duration-150 ${
        active
          ? 'bg-[#2C2C2E] text-[#0A84FF]'
          : 'text-gray-300 hover:bg-[#2C2C2E] hover:text-[#0A84FF]'
      }`}
      onClick={() => {
        const mobileMenu = document.querySelector('.mobile-menu');
        if (mobileMenu) {
          mobileMenu.classList.add('hidden');
        }
      }}
    >
      {icon}
      <span>{label}</span>
    </Link>
  );
};

export default NavBar;