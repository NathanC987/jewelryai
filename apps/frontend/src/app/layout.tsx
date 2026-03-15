import type { Metadata } from "next";
import "./styles.css";

export const metadata: Metadata = {
  title: "JewelryAI MVP",
  description: "Ring customization MVP shell",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className="h-full">
      <body className="app">
        <header className="app-header">
          <div className="app-header__brand">
            <span className="app-logo" aria-hidden="true">
              💍
            </span>
            <div>
              <div className="app-title">JewelryAI</div>
              <div className="app-subtitle">Ring design studio</div>
            </div>
          </div>
          <div className="app-header__meta">
            <span className="app-version">MVP</span>
          </div>
        </header>

        <div className="app-content">{children}</div>
      </body>
    </html>
  );
}
