import type { ReactNode } from "react";
import type { Metadata } from "next";
import { GeistSans } from "geist/font/sans";
import { GeistMono } from "geist/font/mono";
import "./globals.css";
import { AuthProvider } from "@/context/AuthContext";
import AppContentClient from "@/components/AppContentClient";
export const metadata: Metadata = {
  title: "Sistema de Ventas",
  description: "Sistema integral de gestión de ventas",
  generator: "v0.app",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="es">
      <head>
        <style>{`
          html {
            font-family: ${GeistSans.style.fontFamily};
            --font-sans: ${GeistSans.variable};
            --font-mono: ${GeistMono.variable};
          }
        `}</style>
      </head>
      <body className={`min-h-screen ${GeistSans.variable} ${GeistMono.variable}`}>
        <AuthProvider>
          <AppContentClient>{children}</AppContentClient>
        </AuthProvider>
      </body>
    </html>
  );
}