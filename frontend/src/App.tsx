import React, { useEffect, useState } from "react";
import { Chat } from "./components/Chat";
import { API_BASE_URL } from "./config";

interface MetaResponse {
  last_updated?: string | null;
}

const SUPPORTED_FUNDS: string[] = [
  "Bandhan Large Cap Fund Direct Growth",
  "Bandhan Large & Mid Cap Fund Direct Growth",
  "ICICI Prudential Large & Mid Cap Fund Direct Plan Growth",
  "ITI ELSS Tax Saver Fund Direct Growth",
  "ITI Flexi Cap Fund Direct Growth"
];

export const App: React.FC = () => {
  const [lastUpdated, setLastUpdated] = useState<string | null>(null);
  const [presetQuestion, setPresetQuestion] = useState<string | null>(null);

  useEffect(() => {
    const fetchMeta = async () => {
      try {
        const resp = await fetch(`${API_BASE_URL}/meta`);
        if (!resp.ok) return;
        const data: MetaResponse = await resp.json();
        if (data.last_updated) {
          setLastUpdated(data.last_updated);
        }
      } catch {
        // Ignore meta errors; chat will still function.
      }
    };
    fetchMeta();
  }, []);

  const formattedLastUpdated =
    lastUpdated && !Number.isNaN(Date.parse(lastUpdated))
      ? new Date(lastUpdated).toLocaleString()
      : lastUpdated;

  const handleFundClick = (name: string) => {
    const q = `What is the expense ratio, minimum SIP and exit load for ${name}?`;
    setPresetQuestion(q);
  };

  return (
    <div className="app-root">
      <header className="app-header">
        <div className="app-header-content">
          <div className="app-header-brand">
            <div className="app-logo">G</div>
            <div className="app-brand-text">
              <h1>Groww Mutual Fund RAG Chatbot</h1>
              <span className="app-brand-subtitle">MF Facts · Powered by RAG</span>
            </div>
          </div>
          <div className="app-header-note">
            <strong>Note:</strong> Ask factual questions about supported Groww mutual funds. Every answer comes from official Groww pages. No investment advice.
          </div>
          <div className="app-header-funds">
            <span className="app-header-funds-label">Supported funds:</span>
            <div className="app-header-funds-list">
              {SUPPORTED_FUNDS.map(name => (
                <button
                  key={name}
                  type="button"
                  className="app-header-fund-pill"
                  onClick={() => handleFundClick(name)}
                >
                  <span className="app-header-fund-icon" aria-hidden="true">
                    <svg
                      width="18"
                      height="18"
                      viewBox="0 0 24 24"
                      fill="none"
                      xmlns="http://www.w3.org/2000/svg"
                    >
                      <rect x="3" y="11" width="3.5" height="9" rx="1" fill="#4f46e5" />
                      <rect x="9" y="7" width="3.5" height="13" rx="1" fill="#22c55e" />
                      <rect x="15" y="4" width="3.5" height="16" rx="1" fill="#0ea5e9" />
                    </svg>
                  </span>
                  <span className="app-header-fund-name">{name}</span>
                </button>
              ))}
            </div>
          </div>
          {formattedLastUpdated && (
            <p className="app-header-last-updated">
              Last updated: {formattedLastUpdated}
            </p>
          )}
        </div>
      </header>
      <main className="app-main">
        <Chat
          externalQuestion={presetQuestion}
          onExternalQuestionConsumed={() => setPresetQuestion(null)}
        />
      </main>
    </div>
  );
};

