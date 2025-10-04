import Link from 'next/link';
import { Popover, PopoverButton, PopoverPanel } from '@headlessui/react';
import { Bars3Icon, XMarkIcon } from '@heroicons/react/24/outline';

const navigation = [
  { name: 'Home', href: '/' },
  { name: 'Dashboard', href: '/dashboard' },
];

export default function Navbar() {
  return (
    <header className="sticky top-0 z-50 backdrop-blur-sm bg-white/90">
      <Popover className="relative">
        <div className="mx-auto flex max-w-7xl items-center justify-between p-6 lg:px-8">
          <div className="flex justify-start lg:w-0 lg:flex-1">
            <Link href="/">
              <span className="sr-only">Fisher-X</span>
              <div className="flex items-center gap-2">
                <span className="text-2xl font-bold" style={{ color: '#0B3D91' }}>
                  Fisher-X
                </span>
                <span className="text-xs px-2 py-1 rounded" style={{ backgroundColor: '#FC3D21', color: 'white' }}>
                  NASA Space Apps 2025
                </span>
              </div>
            </Link>
          </div>
          
          {/* Mobile menu button */}
          <div className="-my-2 -mr-2 md:hidden">
            <PopoverButton className="relative inline-flex items-center justify-center rounded-md bg-white p-2 text-gray-400 hover:bg-gray-100 hover:text-gray-500 focus:ring-2 focus:ring-inset" style={{ '--tw-ring-color': '#0B3D91' }}>
              <span className="absolute -inset-0.5" />
              <span className="sr-only">Open menu</span>
              <Bars3Icon aria-hidden="true" className="size-6" />
            </PopoverButton>
          </div>
          
          {/* Desktop navigation */}
          <nav className="hidden space-x-10 md:flex">
            {navigation.map((item) => (
              <Link
                key={item.name}
                href={item.href}
                className="text-base font-medium text-gray-500 hover:text-gray-900 transition-colors"
                style={{ '--hover-color': '#0B3D91' }}
              >
                {item.name}
              </Link>
            ))}
          </nav>
        </div>

        {/* Mobile menu panel */}
        <PopoverPanel
          transition
          className="absolute inset-x-0 top-0 z-30 origin-top-right transform p-2 transition data-closed:scale-95 data-closed:opacity-0 data-enter:duration-200 data-enter:ease-out data-leave:duration-100 data-leave:ease-in md:hidden"
        >
          <div className="divide-y-2 divide-gray-50 rounded-lg bg-white shadow-lg ring-1 ring-black/5">
            <div className="px-5 pt-5 pb-6">
              <div className="flex items-center justify-between">
                <div>
                  <span className="text-xl font-bold" style={{ color: '#0B3D91' }}>Fisher-X</span>
                </div>
                <div className="-mr-2">
                  <PopoverButton className="relative inline-flex items-center justify-center rounded-md bg-white p-2 text-gray-400 hover:bg-gray-100 hover:text-gray-500 focus:ring-2 focus:ring-inset" style={{ '--tw-ring-color': '#0B3D91' }}>
                    <span className="absolute -inset-0.5" />
                    <span className="sr-only">Close menu</span>
                    <XMarkIcon aria-hidden="true" className="size-6" />
                  </PopoverButton>
                </div>
              </div>
              <div className="mt-6">
                <nav className="grid grid-cols-1 gap-7">
                  {navigation.map((item) => (
                    <Link
                      key={item.name}
                      href={item.href}
                      className="-m-3 flex items-center rounded-lg p-3 hover:bg-gray-50"
                    >
                      <div className="ml-4 text-base font-medium text-gray-900">{item.name}</div>
                    </Link>
                  ))}
                </nav>
              </div>
            </div>
          </div>
        </PopoverPanel>
      </Popover>
    </header>
  );
}