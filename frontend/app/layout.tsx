import type { Metadata } from "next";
import { Lexend } from "next/font/google";
import { PrimeReactProvider } from "primereact/api";
import "primereact/resources/primereact.min.css";
import "./globals.css";
import "./theme.css";

const lexend = Lexend({ subsets: ["latin"] });

export const metadata: Metadata = {
	title: "2024 MBHS NCAA March Madness Mania",
	description: "Generated by create next app",
};

export default function RootLayout({
	children,
}: Readonly<{
	children: React.ReactNode;
}>) {

	return (
		<html lang="en">
			<PrimeReactProvider>
				<body className={lexend.className}>{children}</body>
			</PrimeReactProvider>
		</html>
	);
}
