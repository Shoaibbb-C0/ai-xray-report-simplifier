import "./globals.css";
import SiteHeader from '@/components/SiteHeader';

export const metadata = {
  title: "AI X-Ray | Patient Support Intelligence",
  description:
    "Foundational patient-support X-ray platform powered by dedicated in-house machine learning models.",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>
        <SiteHeader />
        <div id="main-content">{children}</div>
      </body>
    </html>
  );
}
