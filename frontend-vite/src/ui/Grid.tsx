/**
 * Simple CSS-grid wrapper and cell for consistent dashboard card layouts.
 */
import styles from "../Styles/rt.module.css"
import cn from "../utils/cn"

type Props = {
	children: React.ReactNode
	className?: string
}

export function Grid({ children, className }: Props) {
	return <div className={cn(styles.grid, className)}>{children}</div>
}

export function GridItem({ children, className }: Props) {
	return <div className={cn(styles.gridItem, className)}>{children}</div>
}

