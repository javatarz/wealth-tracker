import { render, screen, cleanup } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import HealthPage from "./HealthPage";

describe("HealthPage", () => {
  const __fetch = globalThis.fetch;

  afterEach(() => {
    cleanup();
    globalThis.fetch = __fetch;
  });

  it("shows loading state initially", () => {
    const never = new Promise<Response>(() => {});
    globalThis.fetch = vi.fn().mockReturnValue(never);
    render(<HealthPage />);
    expect(screen.getByText("Loading health…")).toBeInTheDocument();
  });

  it("renders status and version on successful health check", async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ status: "ok", version: "0.0.1", schema_revision: null }),
    });

    render(<HealthPage />);
    expect(await screen.findByText("ok")).toBeInTheDocument();
    expect(screen.getByText("0.0.1")).toBeInTheDocument();
  });

  it("shows error message when health check fails", async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 500,
      json: async () => ({}),
    });

    render(<HealthPage />);
    expect(await screen.findByRole("alert")).toHaveTextContent("Health check failed: HTTP 500");
  });

  it("shows error message when fetch rejects", async () => {
    globalThis.fetch = vi.fn().mockRejectedValue(new Error("Network down"));

    render(<HealthPage />);
    expect(await screen.findByRole("alert")).toHaveTextContent("Health check failed: Network down");
  });
});
