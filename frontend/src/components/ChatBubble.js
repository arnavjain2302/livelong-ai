function ChatBubble({ message }) {
  return (
    <article className={`chat-bubble ${message.role}`}>
      <span className="chat-role">
        {message.role === 'assistant' ? 'AI Assistant' : 'You'}
      </span>
      <p>{message.content}</p>
    </article>
  );
}

export default ChatBubble;
