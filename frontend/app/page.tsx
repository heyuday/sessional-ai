import Link from "next/link";

export default function Home() {
  return (
    <div className="min-h-screen bg-[#f5f1e8] px-4 py-10">
      <main className="mx-auto max-w-2xl rounded-3xl border border-slate-200 bg-white p-8 shadow-sm">
        <h1 className="text-center text-5xl font-semibold tracking-tight text-slate-900">
          Sessional
        </h1>
        <p className="mt-4 text-center text-lg text-slate-700">
          Select your role to continue to sign in.
        </p>

        <div className="mt-8 grid gap-4 sm:grid-cols-2">
          <Link
            href="/auth/patient"
            className="rounded-2xl border border-blue-200 bg-blue-50 px-6 py-5 text-center text-lg font-semibold text-blue-800 hover:bg-blue-100"
          >
            I am a Patient
          </Link>
          <Link
            href="/auth/clinician"
            className="rounded-2xl border border-slate-300 bg-slate-50 px-6 py-5 text-center text-lg font-semibold text-slate-800 hover:bg-slate-100"
          >
            I am a Clinician
          </Link>
        </div>
      </main>
    </div>
  );
}
