export const metadata = {
    title: 'Dashboard - Fisher-X',
    description: 'Air quality monitoring dashboard',
  };
  
  export default function DashboardLayout({ children }) {
    return (
      <div className="min-h-screen">
        {children}
      </div>
    );
  }