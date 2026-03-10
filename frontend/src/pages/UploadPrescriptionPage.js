import { useState } from 'react';
import LoadingSpinner from '../components/LoadingSpinner';
import InfoCard from '../components/InfoCard';

function toDisplayText(value) {
  if (value == null) {
    return '';
  }

  if (typeof value === 'string' || typeof value === 'number') {
    return String(value);
  }

  if (Array.isArray(value)) {
    return value.map(toDisplayText).filter(Boolean).join(', ');
  }

  if (typeof value === 'object') {
    if (value.name && value.frequency) {
      return [value.name, value.frequency].filter(Boolean).join(' - ');
    }

    return Object.entries(value)
      .map(([key, entryValue]) => `${key}: ${toDisplayText(entryValue)}`)
      .join(', ');
  }

  return String(value);
}

function extractMedicationDetails(medication) {
  const frequencyText = toDisplayText(medication.frequency);
  const frequency = frequencyText.toLowerCase();
  const details = [];

  if (frequency.includes('morning')) {
    details.push({ label: 'Morning', value: '1 tablet' });
  }

  if (frequency.includes('afternoon')) {
    details.push({ label: 'Afternoon', value: '1 tablet' });
  }

  if (frequency.includes('night') || frequency.includes('dinner')) {
    details.push({ label: 'Night', value: '1 tablet' });
  }

  if (frequency.includes('bedtime')) {
    details.push({ label: 'Bedtime', value: '1 tablet' });
  }

  if (!details.length && frequencyText) {
    details.push({ label: 'Instructions', value: frequencyText });
  }

  const durationMatch = frequency.match(
    /(\d+\s*(day|days|week|weeks|month|months))/
  );

  details.push({
    label: 'Duration',
    value: durationMatch ? durationMatch[1] : 'Not specified',
  });

  return details;
}

function getMedicationTitle(medication) {
  if (typeof medication === 'string') {
    return medication;
  }

  return [
    toDisplayText(medication?.name),
    toDisplayText(medication?.dose),
  ]
    .filter(Boolean)
    .join(' ') || 'Unnamed medication';
}

function getTestTitle(test) {
  if (typeof test === 'string') {
    return test;
  }

  if (test?.name) {
    return toDisplayText(test.name);
  }

  return toDisplayText(test) || 'Unnamed test';
}

function getTestSubtitle(test) {
  if (typeof test === 'object' && test !== null) {
    const details = Object.entries(test)
      .filter(([key]) => key !== 'name')
      .map(([key, value]) => `${key}: ${toDisplayText(value)}`);

    if (details.length) {
      return details.join(' | ');
    }
  }

  return 'Requested from uploaded prescription';
}

function UploadPrescriptionPage({
  selectedFile,
  onFileSelect,
  onUpload,
  uploadResult,
  uploadError,
  isUploading,
}) {
  const [isDragging, setIsDragging] = useState(false);

  const medications = uploadResult?.structured_data?.medications || [];
  const tests = uploadResult?.structured_data?.tests || [];

  const handleFiles = (files) => {
    const nextFile = files?.[0];
    if (nextFile) {
      onFileSelect(nextFile);
    }
  };

  const handleDrop = (event) => {
    event.preventDefault();
    setIsDragging(false);
    handleFiles(event.dataTransfer.files);
  };

  const handleDragOver = (event) => {
    event.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (event) => {
    event.preventDefault();
    setIsDragging(false);
  };

  const handleSubmit = (event) => {
    event.preventDefault();
    onUpload();
  };

  return (
    <section className="page-grid">
      <article className="panel panel-large">
        <div className="panel-header">
          <div>
            <p className="panel-kicker">Upload Prescription</p>
            <h2>Prescription extraction</h2>
          </div>
        </div>

        <form className="upload-stack" onSubmit={handleSubmit}>
          <label
            className={`dropzone ${isDragging ? 'dragging' : ''}`}
            htmlFor="prescription-upload"
            onDrop={handleDrop}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
          >
            <input
              id="prescription-upload"
              type="file"
              accept=".pdf"
              onChange={(event) => handleFiles(event.target.files)}
            />
            <div className="dropzone-icon">+</div>
            <strong>
              {selectedFile ? selectedFile.name : 'Drag and drop a PDF here'}
            </strong>
            <p>Or click to browse and upload a prescription document.</p>
          </label>

          <button type="submit" className="primary-button" disabled={isUploading}>
            {isUploading ? 'Processing...' : 'Upload Prescription'}
          </button>
        </form>

        {isUploading ? <LoadingSpinner label="Extracting medications and building care plan" /> : null}
        {uploadError ? <p className="error-text">{uploadError}</p> : null}

        <div className="summary-grid">
          <InfoCard
            title="Selected file"
            value={selectedFile ? 'Ready' : 'None'}
            subtitle={selectedFile?.name || 'Choose a PDF to begin'}
          />
          <InfoCard
            title="Medications found"
            value={String(medications.length)}
            subtitle="Parsed from prescription"
          />
          <InfoCard
            title="Tests found"
            value={String(tests.length)}
            subtitle="Ready for review"
          />
        </div>
      </article>

      <div className="results-column">
        <article className="panel">
          <div className="panel-header">
            <div>
              <p className="panel-kicker">Extracted Medications</p>
              <h2>Medication cards</h2>
            </div>
          </div>

          {medications.length ? (
            <div className="card-stack">
              {medications.map((medication, index) => (
                <article
                  className="result-card"
                  key={`${getMedicationTitle(medication)}-${index}`}
                >
                  <strong>{getMedicationTitle(medication)}</strong>
                  <div className="medication-detail-list">
                    {extractMedicationDetails(medication).map((detail) => (
                      <div
                        className="medication-detail-row"
                        key={`${detail.label}-${detail.value}`}
                      >
                        <span>{detail.label}</span>
                        <p>{detail.value}</p>
                      </div>
                    ))}
                  </div>
                </article>
              ))}
            </div>
          ) : (
            <p className="empty-state">
              Uploaded medications will appear here as individual cards.
            </p>
          )}
        </article>

        <article className="panel">
          <div className="panel-header">
            <div>
              <p className="panel-kicker">Extracted Tests</p>
              <h2>Requested investigations</h2>
            </div>
          </div>

          {tests.length ? (
            <div className="card-stack compact">
              {tests.map((test, index) => (
                <article
                  className="result-card compact"
                  key={`${getTestTitle(test)}-${index}`}
                >
                  <strong>{getTestTitle(test)}</strong>
                  <span>{getTestSubtitle(test)}</span>
                </article>
              ))}
            </div>
          ) : (
            <p className="empty-state">
              Tests and investigations from the prescription will appear here.
            </p>
          )}
        </article>
      </div>
    </section>
  );
}

export default UploadPrescriptionPage;
