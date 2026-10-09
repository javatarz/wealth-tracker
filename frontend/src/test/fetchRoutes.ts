import { vi } from "vitest";

type Route = (request: Request) => Response | Promise<Response>;

export function respond(status: number, body: unknown) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

/** Stubs fetch, answering each request by its "METHOD /path" key. */
export function stubRoutes(routes: Record<string, Route>) {
  const fetchMock = vi.fn((request: Request) => {
    const route = routes[`${request.method} ${new URL(request.url).pathname}`];
    return route
      ? Promise.resolve(route(request))
      : Promise.reject(new TypeError(`Unrouted ${request.url}`));
  });
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}
