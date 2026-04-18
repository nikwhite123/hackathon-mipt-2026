/** Tiny `clsx`-style helper: join truthy class names. */
export default function cn(...classes: Array<string | false | null | undefined>): string {
	return classes.filter(Boolean).join(' ')
}

