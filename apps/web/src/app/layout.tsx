import type { Metadata } from "next";
import { Noto_Sans_SC, Sora } from "next/font/google";
import "@/styles/globals.css";

const sora = Sora({
  subsets: ["latin"],
  weight: ["500", "600", "700"],
  variable: "--font-sora",
  display: "swap",
});

const notoSansSc = Noto_Sans_SC({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-noto",
  display: "swap",
});

export const metadata: Metadata = {
  title: "Prism",
  description: "多模态 Agent · 创作对话 · 知识库 · 资产中心",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="zh-CN">
      <body className={`${sora.variable} ${notoSansSc.variable}`}>
        {children}
      </body>
    </html>
  );
}
