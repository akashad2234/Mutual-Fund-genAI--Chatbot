import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { Chat } from "./Chat";

describe("Chat component", () => {
  it("sends a message and renders assistant response with sources", async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        answer: "22.21% is the 3-year return for this fund.",
        sources: [
          "https://groww.in/mutual-funds/icici-prudential-top-100-fund-direct-growth"
        ],
        question_type: "attribute_query",
        funds: ["icici-prudential-top-100-fund-direct-growth"]
      })
    } as Response);

    // @ts-expect-error override global fetch for test
    global.fetch = mockFetch;

    render(<Chat />);

    const input = screen.getByLabelText("Chat input") as HTMLInputElement;
    const button = screen.getByRole("button", { name: /send/i });

    fireEvent.change(input, {
      target: {
        value:
          "what is the % of return in 3year for https://groww.in/mutual-funds/icici-prudential-top-100-fund-direct-growth MF"
      }
    });
    fireEvent.click(button);

    await waitFor(() =>
      expect(
        screen.getByText(/22.21% is the 3-year return for this fund\./i)
      ).toBeInTheDocument()
    );

    expect(
      screen.getByText(
        "https://groww.in/mutual-funds/icici-prudential-top-100-fund-direct-growth"
      )
    ).toBeInTheDocument();

    expect(mockFetch).toHaveBeenCalledTimes(1);
  });
});

