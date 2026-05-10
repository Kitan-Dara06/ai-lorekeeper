import type { Metadata } from "next";
import "./globals.css";
import { AuthProvider } from "./providers";
import Navbar from "@/components/Navbar";

export const metadata: Metadata = {
  title: "AI Lorekeeper — Your Life, Synthesized",
  description:
    "Upload fragments of your digital life and transform them into structured narrative: story arcs, recurring themes, emotional patterns, and mindset shifts.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="bg-lore-dark text-lore-text antialiased">
        <AuthProvider>
          <Navbar />
          <main className="pt-16 min-h-screen">{children}</main>
        </AuthProvider>
      </body>
    </html>
  );
}
