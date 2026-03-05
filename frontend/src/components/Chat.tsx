import React, { useEffect, useState } from "react";
import { API_BASE_URL } from "../config";

type Role = "user" | "assistant";

interface Message {
  id: string;
  role: Role;
  content: string;
  sources?: string[];
}

interface ChatResponse {
  answer: string;
  sources: string[];
  question_type: string;
  funds: string[];
}

const SUGGESTIONS: string[] = [
  "What is the expense ratio and minimum SIP for Bandhan Large Cap Fund direct growth?",
  "What is the % of return in 3 year for https://groww.in/mutual-funds/icici-prudential-top-100-fund-direct-growth MF?",
  "What is the exit load and benchmark for Bandhan Large & Mid Cap Fund direct growth?",
  "How can I download my mutual fund statement on Groww?"
];

interface ChatProps {
  externalQuestion?: string | null;
  onExternalQuestionConsumed?: () => void;
}

export const Chat: React.FC<ChatProps> = ({
  externalQuestion,
  onExternalQuestionConsumed
}) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showSuggestions, setShowSuggestions] = useState(true);

  const sendMessage = async (text: string) => {
    const trimmed = text.trim();
    if (!trimmed) return;

    setError(null);

    const userMessage: Message = {
      id: crypto.randomUUID(),
      role: "user",
      content: trimmed
    };
    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);

    try {
      const resp = await fetch(`${API_BASE_URL}/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ message: trimmed })
      });

      if (!resp.ok) {
        throw new Error(`API error: ${resp.status}`);
      }

      const data: ChatResponse = await resp.json();
      const assistantMessage: Message = {
        id: crypto.randomUUID(),
        role: "assistant",
        content: data.answer,
        sources: data.sources
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (err: any) {
      console.error(err);
      setError("Something went wrong while contacting the backend.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = input.trim();
    if (!trimmed || isLoading) return;

    setInput("");
    await sendMessage(trimmed);
  };

  const handleSuggestionClick = async (question: string) => {
    if (isLoading) return;
    setShowSuggestions(false);
    await sendMessage(question);
  };

  useEffect(() => {
    if (externalQuestion && !isLoading) {
      setShowSuggestions(false);
      void sendMessage(externalQuestion);
      onExternalQuestionConsumed?.();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [externalQuestion]);

  return (
    <div className="chat-container">
      <div className="chat-window" aria-label="Chat messages">
        {showSuggestions && messages.length === 0 && (
          <div className="chat-suggestions">
            <div className="chat-suggestions-title">Try asking</div>
            <div className="chat-suggestions-list">
              {SUGGESTIONS.map(q => (
                <button
                  key={q}
                  type="button"
                  className="chat-suggestion-item"
                  onClick={() => handleSuggestionClick(q)}
                  disabled={isLoading}
                >
                  <span className="chat-suggestion-icon">→</span>
                  <span className="chat-suggestion-text">{q}</span>
                </button>
              ))}
            </div>
          </div>
        )}
        {messages.map(msg => (
          <div
            key={msg.id}
            className={`chat-message chat-message-${msg.role}`}
          >
            <div className="chat-bubble">
              <div className="chat-role">
                {msg.role === "user" ? "You" : "Assistant"}
              </div>
              <div className="chat-content">{msg.content}</div>
              {msg.role === "assistant" && msg.sources && msg.sources.length > 0 && (
                <div className="chat-sources">
                  <span>Sources:</span>
                  <ul>
                    {msg.sources.map((src, idx) => (
                      <li key={idx}>
                        <a href={src} target="_blank" rel="noreferrer">
                          {src}
                        </a>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </div>
        ))}
        {isLoading && (
          <div className="chat-message chat-message-assistant">
            <div className="chat-bubble chat-bubble-loading">
              <div className="chat-role">Assistant</div>
              <div className="chat-content">Thinking...</div>
            </div>
          </div>
        )}
      </div>

      <form className="chat-input-row" onSubmit={handleSubmit}>
        <input
          aria-label="Chat input"
          className="chat-input"
          type="text"
          placeholder="Ask a question about a Groww mutual fund..."
          value={input}
          onChange={e => setInput(e.target.value)}
          disabled={isLoading}
        />
        <button
          className="chat-send-button"
          type="submit"
          disabled={isLoading || !input.trim()}
          aria-label={isLoading ? "Sending" : "Send"}
        >
          <span aria-hidden="true">{isLoading ? "…" : "↑"}</span>
        </button>
      </form>
      {error && <div className="chat-error">{error}</div>}
    </div>
  );
};

