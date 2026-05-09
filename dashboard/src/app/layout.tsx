import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'Resolution Foundation vs PolicyEngine: Universal Credit comparison',
  description:
    "Compares Resolution Foundation's Universal Credit analysis with PolicyEngine UK microsimulation estimates.",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
