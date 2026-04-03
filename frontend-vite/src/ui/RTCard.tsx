import { Card } from "antd"
import cls from "../Styles/rt.module.css"
import cn from "../utils/cn"

type Props = {
	title?: React.ReactNode
	className?: string
	children: React.ReactNode
	hoverable?: boolean
	onClick?: () => void
	role?: string
	"aria-label"?: string
}

export default function RTCard(props: Props) {
	const { title, className, children, hoverable, onClick, role } = props
	return (
		<Card title={title} className={cn(cls.card, className)} hoverable={hoverable} onClick={onClick} role={role} aria-label={props["aria-label"]}>
			{children}
		</Card>
	)
}

