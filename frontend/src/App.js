import { useState } from 'react';
import './App.css';
import Sidebar from './components/Sidebar';
import UploadPrescriptionPage from './pages/UploadPrescriptionPage';
import CarePlanPage from './pages/CarePlanPage';
import AIAssistantPage from './pages/AIAssistantPage';
import {
  getRequestErrorMessage,
  sendChatMessage,
  uploadPrescription,
} from './services/api';

const NAV_ITEMS = [
  { id: 'upload', label: 'Upload Prescription' },
  { id: 'care-plan', label: 'Care Plan' },
  { id: 'assistant', label: 'AI Assistant' },
];

function App() {
  const [activePage, setActivePage] = useState('upload');
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploadResult, setUploadResult] = useState(null);
  const [uploadError, setUploadError] = useState('');
  const [chatError, setChatError] = useState('');
  const [isUploading, setIsUploading] = useState(false);
  const [isSendingChat, setIsSendingChat] = useState(false);
  const [chatMessages, setChatMessages] = useState([
    {
      role: 'assistant',
      content:
        'I can help explain the care plan, medication timing, and follow-up tasks.',
    },
  ]);

  const handleFileSelect = (file) => {
    setSelectedFile(file);
    setUploadError('');
  };

  const handleUpload = async () => {
    if (!selectedFile) {
      setUploadError('Choose a prescription PDF before uploading.');
      return;
    }

    setIsUploading(true);
    setUploadError('');

    try {
      const data = await uploadPrescription(selectedFile);
      setUploadResult(data);
      setActivePage('care-plan');
    } catch (error) {
      setUploadError(
        getRequestErrorMessage(
          error,
          'Upload failed. Confirm the backend is running and the PDF is valid.'
        )
      );
    } finally {
      setIsUploading(false);
    }
  };

  const handleSendMessage = async (message) => {
    const trimmedMessage = message.trim();
    if (!trimmedMessage) {
      return;
    }

    const nextMessages = [
      ...chatMessages,
      { role: 'user', content: trimmedMessage },
    ];

    setChatMessages(nextMessages);
    setChatError('');
    setIsSendingChat(true);

    try {
      const response = await sendChatMessage(trimmedMessage);
      setChatMessages([
        ...nextMessages,
        {
          role: 'assistant',
          content: response,
        },
      ]);
    } catch (error) {
      setChatError(
        getRequestErrorMessage(
          error,
          'Chat request failed. Confirm the backend is reachable.'
        )
      );
    } finally {
      setIsSendingChat(false);
    }
  };

  const pageProps = {
    selectedFile,
    onFileSelect: handleFileSelect,
    onUpload: handleUpload,
    uploadResult,
    uploadError,
    isUploading,
    chatMessages,
    chatError,
    isSendingChat,
    onSendMessage: handleSendMessage,
  };

  return (
    <div className="dashboard-shell">
      <Sidebar
        items={NAV_ITEMS}
        activePage={activePage}
        onNavigate={setActivePage}
      />

      <main className="dashboard-content">
        <header className="dashboard-header">
          <div>
            <p className="dashboard-kicker">Healthcare AI Dashboard</p>
            <h1>
              {activePage === 'upload' && 'Prescription Intake'}
              {activePage === 'care-plan' && 'Care Plan Overview'}
              {activePage === 'assistant' && 'AI Assistant'}
            </h1>
            <p className="dashboard-subtitle">
              Manage prescription extraction, review the patient care plan, and
              interact with the assistant from a single workspace.
            </p>
          </div>

          <div className="header-badge">
            <span>LiveLong.ai</span>
            <strong>Connected to FastAPI</strong>
          </div>
        </header>

        {activePage === 'upload' && <UploadPrescriptionPage {...pageProps} />}
        {activePage === 'care-plan' && <CarePlanPage uploadResult={uploadResult} />}
        {activePage === 'assistant' && (
          <AIAssistantPage
            chatMessages={chatMessages}
            chatError={chatError}
            isSendingChat={isSendingChat}
            onSendMessage={handleSendMessage}
          />
        )}
      </main>
    </div>
  );
}

export default App;
