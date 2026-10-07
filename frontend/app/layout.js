import "./globals.css";

export const metadata = {
  title: "AI X-Ray | Patient Support Intelligence",
  description:
    "Foundational patient-support X-ray platform powered by dedicated in-house machine learning models.",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen bg-[#0b0d11] text-slate-100 antialiased selection:bg-teal-500/20 selection:text-teal-300">
        {children}
      </body>
    </html>
  );
}
