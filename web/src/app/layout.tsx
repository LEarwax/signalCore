import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "signalCore",
  description: "ERRCS engineering — auto-generate AHJ submittal packets from floor plan PDFs",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="bg-gray-950 text-gray-100 antialiased">
        {children}
      </body>
    </html>
  );
}
