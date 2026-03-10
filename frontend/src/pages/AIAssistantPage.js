import { useEffect, useRef, useState } from 'react';
import ChatBubble from '../components/ChatBubble';

const QUICK_PROMPTS = [
  'What medicines should I take today?',
  'When is my next test?',
  'Explain my prescription',
];

function AIAssistantPage({
  chatMessages,
  chatError,
  isSendingChat,
  onSendMessage,
}) {
  const [message, setMessage] = useState('');
  const threadRef = useRef(null);

  useEffect(() => {
    if (threadRef.current) {
      threadRef.current.scrollTop = threadRef.current.scrollHeight;
    }
  }, [chatMessages, isSendingChat]);

  const handleSubmit = (event) => {
    event.preventDefault();
    onSendMessage(message);
    setMessage('');
  };

  const handleQuickPrompt = (prompt) => {
    onSendMessage(prompt);
  };

  return (
    <section className="assistant-layout">
      <article className="panel assistant-panel">
        <div className="panel-header">
          <div>
            <p className="panel-kicker">AI Assistant</p>
            <h2>Conversation</h2>
          </div>
        </div>

        <div className="chat-history" ref={threadRef}>
          {chatMessages.map((chatMessage, index) => (
            <ChatBubble key={`${chatMessage.role}-${index}`} message={chatMessage} />
          ))}
          {isSendingChat ? (
            <div className="chat-typing" role="status" aria-live="polite">
              <span className="typing-dots">
                <span />
                <span />
                <span />
              </span>
              <span>AI Assistant is thinking...</span>
            </div>
          ) : null}
        </div>

        <div className="quick-prompts">
          {QUICK_PROMPTS.map((prompt) => (
            <button
              key={prompt}
              type="button"
              className="quick-prompt-button"
              onClick={() => handleQuickPrompt(prompt)}
              disabled={isSendingChat}
            >
              {prompt}
            </button>
          ))}
        </div>

        <form className="chat-input-bar" onSubmit={handleSubmit}>
          <textarea
            value={message}
            onChange={(event) => setMessage(event.target.value)}
            rows="3"
            placeholder="Ask about medications, monitoring, or follow-up guidance."
          />
          <button
            type="submit"
            className="primary-button"
            disabled={isSendingChat}
          >
            Send
          </button>
        </form>

        {chatError ? <p className="error-text">{chatError}</p> : null}
      </article>
    </section>
  );
}

export default AIAssistantPage;
