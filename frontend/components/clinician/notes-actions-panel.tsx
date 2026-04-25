export function NotesActionsPanel() {
  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-5">
      <h2 className="text-xl font-semibold text-slate-900">Clinician Notes + actions</h2>
      <label className="mt-3 block text-sm font-medium text-slate-700" htmlFor="notes">
        Private notes
      </label>
      <textarea
        id="notes"
        rows={4}
        placeholder="Review cognitive behavioral approach. Check on medication compliance."
        className="mt-2 w-full rounded-xl border border-slate-300 px-3 py-2 text-sm text-slate-800 focus:border-blue-500 focus:outline-none"
      />
      <div className="mt-3 flex flex-wrap gap-2">
        {["Follow-up", "Sleep", "Medication", "Trauma"].map((flag) => (
          <button
            key={flag}
            type="button"
            className="rounded-lg border border-slate-200 bg-slate-50 px-3 py-1 text-xs font-medium text-slate-700"
          >
            {flag}
          </button>
        ))}
      </div>
      <button
        type="button"
        className="mt-4 w-full rounded-xl bg-blue-600 px-4 py-3 text-sm font-semibold text-white hover:bg-blue-700"
      >
        Mark Reviewed
      </button>
    </section>
  );
}
