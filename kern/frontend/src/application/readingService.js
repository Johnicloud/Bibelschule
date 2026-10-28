// Anwendungsschicht: Lesenachweis. Bringt Formularwerte in die Form, die der Dienst erwartet.
function taskBody(t, buecher) {
  return {
    title: t.title.trim(),
    unit: t.unit,
    total: buecher ? null : Number(t.total),
    passes: Number(t.passes) || 1,
    start: t.start || null,
    deadline: t.deadline || null,
    buecher: buecher ? buecher.map((b) => ({ title: b.title.trim(), total: Number(b.total) })) : null,
  }
}

export function createReadingService(api) {
  return {
    list: (subjectId) => api.tasks(subjectId),
    status: (subjectId) => api.status(subjectId), // Lesestatus des ganzen Fachs
    add: (subjectId, t, buecher = null) => api.addTask({ subject_id: subjectId, ...taskBody(t, buecher) }),
    update: (id, t, buecher = null) => api.updateTask(id, taskBody(t, buecher)),
    remove: (id) => api.deleteTask(id),
    setSkript: (id, skriptId) => api.setSkript(id, skriptId),   // Datei aus dem Reiter „Skripte“ ans Pensum hängen (null löst sie)
    log: (id, e) => api.log(id, { amount: Number(e.amount), day: e.day || null, buch_id: e.buchId || null,
      durchlauf: e.durchlauf ? Number(e.durchlauf) : 1 }),
    deleteEntry: (id, entryId) => api.deleteEntry(id, entryId),
  }
}
