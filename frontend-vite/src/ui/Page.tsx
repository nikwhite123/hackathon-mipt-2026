import { Typography } from "antd"
import styles from "../Styles/rt.module.css"

type Props = {
	title?: string
	subtitle?: string
	children: React.ReactNode
}

export default function Page({ title, subtitle, children }: Props) {
	return (
		<div className={styles.page}>
			{title && (
				<div className={styles.pageHeader}>
					<Typography.Title level={3} className={styles.pageTitle}>{title}</Typography.Title>
					{subtitle && <Typography.Paragraph className={styles.pageSubtitle}>{subtitle}</Typography.Paragraph>}
				</div>
			)}
			<div className={styles.pageBody}>{children}</div>
		</div>
	)
}

