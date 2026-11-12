import { afterEach, describe, expect, it, vi } from "vitest";
import { createSparqlClient } from "./sparqlClient";

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("createSparqlClient", () => {
  it("loads every recorded SPARQL query", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify({
          pair_id: "p1",
          queries: ["SELECT * WHERE { ?s ?p ?o }", "ASK { ?s ?p ?o }"],
        }),
        { status: 200 },
      ),
    );
    vi.stubGlobal("fetch", fetchMock);

    const queries = await createSparqlClient("/api/threads/").getSparql("s1", "p1");

    expect(fetchMock).toHaveBeenCalledWith("/api/threads/s1/pairs/p1/sparql");
    expect(queries).toEqual(["SELECT * WHERE { ?s ?p ?o }", "ASK { ?s ?p ?o }"]);
  });

  it("returns an empty list when the response has no queries", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(JSON.stringify({ pair_id: "p1", queries: [] }), {
          status: 200,
        }),
      ),
    );

    const queries = await createSparqlClient("/api/threads").getSparql("s1", "p1");

    expect(queries).toEqual([]);
  });

  it("throws on a failed SPARQL request", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response("", { status: 500 })));

    await expect(createSparqlClient("/api/threads").getSparql("s1", "p1")).rejects.toThrow(
      "status 500",
    );
  });
});
