import { ConfigProvider, theme } from "antd"
import React from "react"

type Props = {
	children: React.ReactNode
}

export function RTThemeProvider({ children }: Props) {
	return (
		<ConfigProvider
			theme={{
				algorithm: theme.defaultAlgorithm,
				token: {
					colorPrimary: "#FF4F00",
					colorInfo: "#FF4F00",
					colorText: "#1f2937",
					colorTextHeading: "#0b1324",
					colorBorder: "#e5e7eb",
					colorBgBase: "#ffffff",
					fontFamily: "Inter, system-ui, 'Segoe UI', Roboto, Arial, sans-serif",
					borderRadius: 8
				},
				components: {
					Layout: {
						headerBg: "#0b1f33",
						bodyBg: "#ffffff",
						siderBg: "#0b1f33"
					},
					Menu: {
						itemSelectedBg: "rgba(255,79,0,0.12)",
						itemSelectedColor: "#ffffff",
						itemHoverColor: "#ffffff",
						itemColor: "rgba(255,255,255,0.85)"
					},
					Button: {
						controlHeight: 40
					},
					Card: {
						padding: 16,
						colorBorderSecondary: "#eef0f3"
					},
					Select: {
						controlHeight: 40
					},
					Input: {
						controlHeight: 40
					}
				}
			}}
		>
			{children}
		</ConfigProvider>
	)
}

