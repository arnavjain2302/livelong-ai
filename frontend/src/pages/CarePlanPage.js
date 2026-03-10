function parseTimeToMinutes(value) {
  if (!value || !value.includes(':')) {
    return Number.MAX_SAFE_INTEGER;
  }

  const [hours, minutes] = value.split(':').map(Number);
  return hours * 60 + minutes;
}

function getNextMedicationIndex(schedule) {
  if (!schedule.length) {
    return -1;
  }

  const now = new Date();
  const currentMinutes = now.getHours() * 60 + now.getMinutes();
  const nextIndex = schedule.findIndex(
    (item) => parseTimeToMinutes(item.time) >= currentMinutes
  );

  return nextIndex >= 0 ? nextIndex : 0;
}

function CarePlanPage({ uploadResult }) {
  const schedule = uploadResult?.care_plan?.daily_schedule || [];
  const monitoring = uploadResult?.care_plan?.monitoring || [];
  const followUp = uploadResult?.care_plan?.follow_up || '';
  const nextMedicationIndex = getNextMedicationIndex(schedule);
  const nextMonitoring = monitoring[0];
  const nextFollowUp = followUp || 'Not scheduled yet';

  return (
    <section className="care-plan-grid">
      <article className="panel summary-panel">
        <div className="panel-header">
          <div>
            <p className="panel-kicker">Today's Health Summary</p>
            <h2>Quick overview</h2>
          </div>
        </div>

        <div className="summary-overview">
          <div className="summary-overview-item">
            <span>Medications today</span>
            <strong>{schedule.length}</strong>
          </div>
          <div className="summary-overview-item">
            <span>Next test</span>
            <strong>
              {nextMonitoring
                ? `${nextMonitoring.task || 'Scheduled task'}${
                    nextMonitoring.day ? ` (${nextMonitoring.day})` : ''
                  }`
                : 'No test scheduled'}
            </strong>
          </div>
          <div className="summary-overview-item">
            <span>Next follow-up</span>
            <strong>{nextFollowUp}</strong>
          </div>
          <div className="summary-overview-item">
            <span>Reminder status</span>
            <strong>Daily reminders active</strong>
          </div>
        </div>
      </article>

      <article className="panel">
        <div className="panel-header">
          <div>
            <p className="panel-kicker">Medication Schedule</p>
            <h2>Timeline</h2>
          </div>
        </div>

        {schedule.length ? (
          <div className="timeline-list">
            {schedule.map((item, index) => (
              <div
                className={`timeline-item ${index === nextMedicationIndex ? 'next-dose' : ''}`}
                key={`${item.time}-${index}`}
              >
                <span className="timeline-label">{item.time}</span>
                <div>
                  <div className="timeline-title-row">
                    <strong>{item.task}</strong>
                    {index === nextMedicationIndex ? (
                      <span className="next-dose-badge">Next Dose</span>
                    ) : null}
                  </div>
                  <p>{item.type}</p>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="empty-state">
            Upload a prescription to generate the medication schedule.
          </p>
        )}
      </article>

      <article className="panel">
        <div className="panel-header">
          <div>
            <p className="panel-kicker">Monitoring Tasks</p>
            <h2>Care checklist</h2>
          </div>
        </div>

        {monitoring.length ? (
          <div className="list-stack">
            {monitoring.map((item, index) => (
              <article className="task-card" key={`${item.day || 'monitor'}-${index}`}>
                <strong>{item.day || 'Scheduled check'}</strong>
                <p>{item.task}</p>
              </article>
            ))}
          </div>
        ) : (
          <p className="empty-state">
            Monitoring tasks will appear here after care plan generation.
          </p>
        )}
      </article>

      <article className="panel">
        <div className="panel-header">
          <div>
            <p className="panel-kicker">Follow-up Plan</p>
            <h2>Next steps</h2>
          </div>
        </div>

        {followUp ? (
          <article className="followup-card">
            <strong>Recommended follow-up</strong>
            <p>{followUp}</p>
          </article>
        ) : (
          <p className="empty-state">
            Follow-up recommendations will appear here after processing.
          </p>
        )}
      </article>
    </section>
  );
}

export default CarePlanPage;
