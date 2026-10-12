export function dueInfo(card) {
  if (card.is_due) return { text: 'Fällig', due: true }
  const days = Math.ceil((new Date(card.due) - Date.now()) / 86400000)
  return { text: days <= 1 ? 'Morgen' : `in ${days} Tagen`, due: false }
}
