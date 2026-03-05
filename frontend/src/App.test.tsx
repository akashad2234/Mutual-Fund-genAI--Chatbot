import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import { App } from "./App";

describe("App header metadata", () => {
  it("shows last updated date from /meta endpoint", async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        last_updated: "2026-03-04T10:00:00Z"
      })
    } as Response);

    // @ts-expect-error override global fetch for test
    global.fetch = mockFetch;

    render(<App />);

    await waitFor(() =>
      expect(screen.getByText(/Last updated:/i)).toBeInTheDocument()
    );
  });
});

