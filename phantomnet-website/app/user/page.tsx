export default function UserPortal() {
  return (
    <main className="min-h-screen bg-pn-dark-blue px-4 pb-16 pt-24 text-pn-text-light md:px-8">
      <section className="mx-auto max-w-3xl rounded-xl border border-pn-border bg-pn-dark-light/55 p-8 shadow-2xl shadow-black/20">
        <p className="font-mono text-xs font-semibold uppercase tracking-[0.2em] text-pn-neon-blue">
          Transparency boundary
        </p>
        <h1 className="mt-3 font-heading text-3xl font-bold text-pn-heading md:text-4xl">
          User security portal is not operational
        </h1>
        <p className="mt-5 leading-7 text-pn-text-muted">
          This route does not display live endpoint posture, telemetry, honeypot state, security tokens,
          vulnerability data, cryptographic audit results, or response controls. Those earlier displays relied
          on retired, simulated, or unsupported client behavior and are intentionally unavailable here.
        </p>

        <div className="mt-8 rounded-lg border border-pn-border bg-pn-dark-blue/80 p-5">
          <h2 className="font-heading text-lg font-semibold text-pn-heading">Supported workflow boundary</h2>
          <p className="mt-3 leading-7 text-pn-text-muted">
            Tenant-scoped analyst workflows must authenticate to their governed service boundary and remain
            evidence-bound, capability-checked, and approval-controlled where a high-impact response is
            involved. This public route does not substitute for that workflow.
          </p>
        </div>

        <a
          className="mt-8 inline-flex rounded-lg border border-pn-neon-blue/40 px-4 py-2 text-sm font-semibold text-pn-neon-blue transition-colors hover:bg-pn-neon-blue/10"
          href="/contact"
        >
          Contact the project team
        </a>
      </section>
    </main>
  );
}
