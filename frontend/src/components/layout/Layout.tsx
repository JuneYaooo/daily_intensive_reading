import React from 'react';
import NavBar from './NavBar';

interface LayoutProps {
  children: React.ReactNode;
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  return (
    <div className="min-h-screen bg-[#F5F5F7]">
      <NavBar />
      <main className="container mx-auto px-4 pt-20 pb-10">
        {children}
      </main>
      <footer className="bg-[#1C1C1E] bg-opacity-90 backdrop-blur-lg text-white py-4">
        <div className="container mx-auto px-4 text-center text-sm">
          <p>© {new Date().getFullYear()} 每日精读 - 您的个性化内容策划工具</p>
        </div>
      </footer>
    </div>
  );
};

export default Layout;