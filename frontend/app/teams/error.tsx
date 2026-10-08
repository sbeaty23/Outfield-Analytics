"use client";

export default function TeamsError({ reset }: { reset: () => void }) {
  return (
    <main className="content-shell">
      <h1>Baseball data is temporarily unavailable</h1>
      <p>Please try again shortly.</p>
      <button onClick={reset}>Try again</button>
    </main>
  );
}
