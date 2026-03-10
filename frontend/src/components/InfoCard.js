function InfoCard({ title, value, subtitle }) {
  return (
    <article className="info-card">
      <span>{title}</span>
      <strong>{value}</strong>
      {subtitle ? <p>{subtitle}</p> : null}
    </article>
  );
}

export default InfoCard;
