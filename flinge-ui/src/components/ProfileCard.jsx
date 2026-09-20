export default function ProfileCard({ profile, proposed }) {
  if (!profile) return <div className="card">Loading deck…</div>;
  return (
    <article className={`card ${profile.danger ? "danger" : ""}`}>
      <div className="avatar" aria-hidden="true">
        {profile.name?.[0] || "?"}
      </div>
      <div>
        <h2>
          {profile.name}
          {profile.age_days != null ? `, ${profile.age_days}d` : ""}
        </h2>
        <div className="vibes">{(profile.vibes || []).join(" · ")}</div>
      </div>
      <div className="prompt-block">
        <p className="prompt-label">{profile.prompt}</p>
        <p className="prompt-answer">{profile.answer}</p>
      </div>
      {proposed ? (
        <p className="footer-line">
          Fly leans: <strong>{proposed.action}</strong>
          {proposed.rizz_bucket ? ` · ${proposed.rizz_bucket}` : ""}
        </p>
      ) : null}
    </article>
  );
}
