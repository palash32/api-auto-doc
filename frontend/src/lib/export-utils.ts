/**
 * Export utilities for generating cURL, HTTPie, and Postman collection formats
 * from API playground requests.
 */

export interface RequestConfig {
    method: string;
    url: string;
    headers: Record<string, string>;
    body?: string;
}

/**
 * Generate a cURL command from a request configuration
 */
export function generateCurl(request: RequestConfig): string {
    const parts: string[] = ["curl"];

    // Add method (skip for GET as it's default)
    if (request.method !== "GET") {
        parts.push(`-X ${request.method}`);
    }

    // Add headers
    Object.entries(request.headers).forEach(([key, value]) => {
        parts.push(`-H "${key}: ${value}"`);
    });

    // Add body for non-GET requests
    if (request.body && request.method !== "GET") {
        // Escape single quotes in body
        const escapedBody = request.body.replace(/'/g, "'\\''");
        parts.push(`-d '${escapedBody}'`);
    }

    // Add URL (quoted for safety)
    parts.push(`"${request.url}"`);

    return parts.join(" \\\n  ");
}

/**
 * Generate an HTTPie command from a request configuration
 */
export function generateHttpie(request: RequestConfig): string {
    const parts: string[] = ["http"];

    // Add method and URL
    parts.push(request.method);
    parts.push(`"${request.url}"`);

    // Add headers (HTTPie uses Key:Value format)
    Object.entries(request.headers).forEach(([key, value]) => {
        parts.push(`"${key}:${value}"`);
    });

    // Add body for POST/PUT/PATCH (HTTPie can auto-serialize JSON)
    if (request.body && ["POST", "PUT", "PATCH"].includes(request.method)) {
        try {
            // If it's valid JSON, use HTTPie's JSON syntax
            const jsonBody = JSON.parse(request.body);
            Object.entries(jsonBody).forEach(([key, value]) => {
                if (typeof value === "string") {
                    parts.push(`${key}="${value}"`);
                } else {
                    parts.push(`${key}:=${JSON.stringify(value)}`);
                }
            });
        } catch {
            // Fallback to raw body
            parts.push(`--raw '${request.body}'`);
        }
    }

    return parts.join(" \\\n  ");
}

/**
 * Generate a Postman Collection v2.1 format
 */
export function generatePostmanCollection(
    requests: RequestConfig[],
    collectionName: string = "API Playground Export"
): object {
    return {
        info: {
            _postman_id: crypto.randomUUID(),
            name: collectionName,
            schema: "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
        },
        item: requests.map((request, index) => ({
            name: `Request ${index + 1}: ${request.method} ${new URL(request.url).pathname}`,
            request: {
                method: request.method,
                header: Object.entries(request.headers).map(([key, value]) => ({
                    key,
                    value,
                    type: "text"
                })),
                body: request.body ? {
                    mode: "raw",
                    raw: request.body,
                    options: {
                        raw: {
                            language: "json"
                        }
                    }
                } : undefined,
                url: {
                    raw: request.url,
                    protocol: new URL(request.url).protocol.replace(":", ""),
                    host: new URL(request.url).hostname.split("."),
                    port: new URL(request.url).port || undefined,
                    path: new URL(request.url).pathname.split("/").filter(Boolean),
                    query: Array.from(new URL(request.url).searchParams.entries()).map(([key, value]) => ({
                        key,
                        value
                    }))
                }
            },
            response: []
        }))
    };
}

/**
 * Generate Insomnia export format (v4)
 */
export function generateInsomnia(
    requests: RequestConfig[],
    workspaceName: string = "API Playground Export"
): object {
    const workspaceId = `wrk_${Date.now()}`;

    return {
        _type: "export",
        __export_format: 4,
        __export_date: new Date().toISOString(),
        __export_source: "api-auto-documentation-platform",
        resources: [
            {
                _id: workspaceId,
                _type: "workspace",
                name: workspaceName,
                description: "Exported from API Auto-Documentation Platform",
                scope: "collection"
            },
            ...requests.map((request, index) => ({
                _id: `req_${Date.now()}_${index}`,
                _type: "request",
                parentId: workspaceId,
                name: `${request.method} ${new URL(request.url).pathname}`,
                method: request.method,
                url: request.url,
                headers: Object.entries(request.headers).map(([name, value]) => ({
                    name,
                    value
                })),
                body: request.body ? {
                    mimeType: "application/json",
                    text: request.body
                } : {}
            }))
        ]
    };
}

/**
 * Generate JavaScript/TypeScript fetch code
 */
export function generateFetch(request: RequestConfig): string {
    const options: string[] = [];

    options.push(`  method: "${request.method}"`);

    if (Object.keys(request.headers).length > 0) {
        const headersStr = JSON.stringify(request.headers, null, 4)
            .split("\n")
            .map((line, i) => i === 0 ? line : "  " + line)
            .join("\n");
        options.push(`  headers: ${headersStr}`);
    }

    if (request.body && request.method !== "GET") {
        options.push(`  body: JSON.stringify(${request.body})`);
    }

    return `fetch("${request.url}", {
${options.join(",\n")}
})
  .then(response => response.json())
  .then(data => console.log(data))
  .catch(error => console.error("Error:", error));`;
}

/**
 * Generate Python requests code
 */
export function generatePython(request: RequestConfig): string {
    const lines: string[] = ["import requests", ""];

    lines.push(`url = "${request.url}"`);

    if (Object.keys(request.headers).length > 0) {
        lines.push(`headers = ${JSON.stringify(request.headers, null, 4)}`);
    }

    if (request.body && request.method !== "GET") {
        lines.push(`payload = ${request.body}`);
    }

    lines.push("");

    const methodLower = request.method.toLowerCase();
    let callParts = [`requests.${methodLower}(url`];

    if (Object.keys(request.headers).length > 0) {
        callParts.push("headers=headers");
    }

    if (request.body && request.method !== "GET") {
        callParts.push("json=payload");
    }

    lines.push(`response = ${callParts.join(", ")})`);
    lines.push("print(response.json())");

    return lines.join("\n");
}

/**
 * Copy text to clipboard with fallback
 */
export async function copyToClipboard(text: string): Promise<boolean> {
    try {
        await navigator.clipboard.writeText(text);
        return true;
    } catch {
        // Fallback for older browsers
        const textArea = document.createElement("textarea");
        textArea.value = text;
        textArea.style.position = "fixed";
        textArea.style.left = "-9999px";
        document.body.appendChild(textArea);
        textArea.select();
        const success = document.execCommand("copy");
        document.body.removeChild(textArea);
        return success;
    }
}

/**
 * Download content as a file
 */
export function downloadAsFile(content: string, filename: string, mimeType: string = "application/json"): void {
    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
}
