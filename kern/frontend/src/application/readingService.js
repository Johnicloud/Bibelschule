// Anwendungsschicht: Lesenachweis. Bringt Formularwerte in die Form, die der Dienst erwartet.
export function createReadingService(api) {
  return {
    list: (subjectId) => api.tasks(subjectId),
    status: (subjectId) => api.status(subjectId), // Lesestatus des ganzen Fachs
    add: (subjectId, t) => api.addTask({
      subject_id: subjectId,
      title: t.title.trim(),
      unit: t.unit,
      total: Number(t.total),
      passes: Number(t.passes) || 1,
      deadline: t.deadline || null,
    }),
    remove: (id) => api.deleteTask(id),
    log: (id, e) => api.log(id, { amount: Number(e.amount), day: e.day || null, note: (e.note || '').trim() }),
    deleteEntry: (id, entryId) => api.deleteEntry(id, entryId),
  }
}
